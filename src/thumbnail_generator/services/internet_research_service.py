"""Research current game information with a non-blocking local fallback."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Any, Iterable
from urllib.parse import urlparse

from ddgs import DDGS

from src.thumbnail_generator.models.video_request import VideoRequest


class InternetResearchError(RuntimeError):
    """Raised when internet research cannot be completed."""


@dataclass(frozen=True, slots=True)
class SearchResult:
    """One normalized internet search result."""

    title: str
    url: str
    summary: str
    domain: str
    query: str


@dataclass(frozen=True, slots=True)
class GameResearch:
    """Structured research for one gameplay video."""

    supplied_game_name: str
    suggested_game_name: str
    game_name_was_corrected: bool
    terminology: tuple[str, ...]
    search_results: tuple[SearchResult, ...]
    queries: tuple[str, ...]
    internet_available: bool
    warning: str | None = None

    @property
    def effective_game_name(self) -> str:
        """Return the corrected or supplied game name."""

        return self.suggested_game_name


def research_video_context_safe(
    request: VideoRequest,
    maximum_results_per_query: int = 5,
) -> GameResearch:
    """Research video context without blocking the main workflow."""

    try:
        return research_video_context(
            request=request,
            maximum_results_per_query=maximum_results_per_query,
        )
    except InternetResearchError as error:
        return _build_local_fallback(
            request=request,
            warning=str(error),
        )
    except Exception as error:
        return _build_local_fallback(
            request=request,
            warning=f"Unexpected internet research error: {error}",
        )


def research_video_context(
    request: VideoRequest,
    maximum_results_per_query: int = 5,
) -> GameResearch:
    """Research current game information for one video request."""

    if maximum_results_per_query < 1:
        raise InternetResearchError(
            "Maximum results per query must be at least one."
        )

    queries = _build_research_queries(request)
    collected_results: list[SearchResult] = []
    search_errors: list[str] = []

    for query in queries:
        try:
            raw_results = _search_text(
                query=query,
                maximum_results=maximum_results_per_query,
            )
        except InternetResearchError as error:
            search_errors.append(str(error))
            continue

        collected_results.extend(
            _normalize_results(
                raw_results=raw_results,
                query=query,
            )
        )

    unique_results = _deduplicate_results(collected_results)

    if not unique_results:
        details = "; ".join(search_errors)

        if details:
            raise InternetResearchError(
                f"Internet research unavailable: {details}"
            )

        raise InternetResearchError(
            "Internet research returned no usable results."
        )

    suggested_game_name = _infer_game_name(
        supplied_game_name=request.game_name,
        results=unique_results,
    )

    terminology = _extract_terminology(
        results=unique_results,
        game_name=suggested_game_name,
    )

    return GameResearch(
        supplied_game_name=request.game_name,
        suggested_game_name=suggested_game_name,
        game_name_was_corrected=(
            _normalize_for_comparison(request.game_name)
            != _normalize_for_comparison(suggested_game_name)
        ),
        terminology=terminology,
        search_results=tuple(unique_results),
        queries=queries,
        internet_available=True,
    )


def _build_local_fallback(
    request: VideoRequest,
    warning: str,
) -> GameResearch:
    """Create safe local research data when internet access fails."""

    supplied_game_name = _clean_text(request.game_name)

    return GameResearch(
        supplied_game_name=supplied_game_name,
        suggested_game_name=supplied_game_name,
        game_name_was_corrected=False,
        terminology=_build_local_terminology(request),
        search_results=(),
        queries=_build_research_queries(request),
        internet_available=False,
        warning=warning,
    )


def _build_local_terminology(
    request: VideoRequest,
) -> tuple[str, ...]:
    """Build basic local terminology from the video request."""

    terms = [
        _clean_text(request.game_name),
        _clean_text(request.video_type),
        _clean_text(request.episode_topic),
        "Gameplay",
        "Gaming",
        "Highlights",
        "Reaction",
    ]

    return _deduplicate_terms(terms)


def _search_text(
    query: str,
    maximum_results: int,
) -> list[dict[str, Any]]:
    """Execute one DDGS text search."""

    try:
        results = DDGS(timeout=8).text(
            query,
            region="wt-wt",
            safesearch="moderate",
            max_results=maximum_results,
            backend="auto",
        )
    except Exception as error:
        raise InternetResearchError(
            f"Search failed for '{query}': {error}"
        ) from error

    if results is None:
        return []

    return [
        result
        for result in results
        if isinstance(result, dict)
    ]


def _build_research_queries(
    request: VideoRequest,
) -> tuple[str, ...]:
    """Build targeted search queries for one video."""

    game_name = _clean_text(request.game_name)
    video_type = _clean_text(request.video_type)
    episode_topic = _clean_text(request.episode_topic)

    return (
        f"{game_name} official game",
        f"{game_name} gameplay terminology",
        f"{game_name} {video_type} {episode_topic}",
        f"{game_name} latest gameplay trends",
    )


def _normalize_results(
    raw_results: Iterable[dict[str, Any]],
    query: str,
) -> list[SearchResult]:
    """Convert DDGS result dictionaries into typed results."""

    normalized_results: list[SearchResult] = []

    for raw_result in raw_results:
        title = _clean_text(
            str(raw_result.get("title") or "")
        )
        url = _clean_text(
            str(
                raw_result.get("href")
                or raw_result.get("url")
                or ""
            )
        )
        summary = _clean_text(
            str(
                raw_result.get("body")
                or raw_result.get("description")
                or ""
            )
        )

        if not title or not url:
            continue

        normalized_results.append(
            SearchResult(
                title=title,
                url=url,
                summary=summary,
                domain=_extract_domain(url),
                query=query,
            )
        )

    return normalized_results


def _deduplicate_results(
    results: Iterable[SearchResult],
) -> list[SearchResult]:
    """Remove duplicate URLs and titles."""

    unique_results: list[SearchResult] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    for result in results:
        normalized_url = result.url.rstrip("/").casefold()
        normalized_title = _normalize_for_comparison(result.title)

        if normalized_url in seen_urls:
            continue

        if normalized_title in seen_titles:
            continue

        seen_urls.add(normalized_url)
        seen_titles.add(normalized_title)
        unique_results.append(result)

    return unique_results


def _infer_game_name(
    supplied_game_name: str,
    results: list[SearchResult],
) -> str:
    """Infer a likely canonical game name from search titles."""

    supplied_clean = _clean_text(supplied_game_name)
    supplied_normalized = _normalize_for_comparison(supplied_clean)
    candidate_scores: dict[str, float] = {}

    for result in results:
        for candidate in _extract_title_candidates(result.title):
            candidate_normalized = _normalize_for_comparison(candidate)

            if not candidate_normalized:
                continue

            similarity = SequenceMatcher(
                None,
                supplied_normalized,
                candidate_normalized,
            ).ratio()

            if similarity < 0.65:
                continue

            score = similarity

            if _is_authoritative_domain(result.domain):
                score += 0.20

            candidate_scores[candidate] = max(
                candidate_scores.get(candidate, 0.0),
                score,
            )

    if not candidate_scores:
        return supplied_clean

    best_candidate = max(
        candidate_scores,
        key=candidate_scores.get,
    )

    if candidate_scores[best_candidate] < 0.78:
        return supplied_clean

    return best_candidate


def _extract_title_candidates(title: str) -> tuple[str, ...]:
    """Extract likely game names from one result title."""

    parts = [title]

    for separator in (" - ", " | ", ": ", " — ", " – "):
        expanded_parts: list[str] = []

        for part in parts:
            expanded_parts.extend(part.split(separator))

        parts = expanded_parts

    candidates: list[str] = []

    for part in parts:
        cleaned_part = re.sub(
            r"\b(?:official|gameplay|wiki|guide|download|trailer)\b",
            "",
            part,
            flags=re.IGNORECASE,
        )
        cleaned_part = _clean_text(cleaned_part)

        if not cleaned_part:
            continue

        if len(cleaned_part) > 45:
            continue

        if not 1 <= len(cleaned_part.split()) <= 6:
            continue

        candidates.append(_title_case_game_name(cleaned_part))

    return tuple(candidates)


def _extract_terminology(
    results: list[SearchResult],
    game_name: str,
    maximum_terms: int = 12,
) -> tuple[str, ...]:
    """Extract conservative gameplay terminology from search results."""

    gaming_vocabulary = {
        "adventure",
        "battle",
        "boss",
        "challenge",
        "character",
        "combat",
        "controller",
        "escape",
        "fail",
        "fight",
        "funniest",
        "funny",
        "highlight",
        "highlights",
        "horror",
        "jump",
        "jumpscare",
        "level",
        "mission",
        "moment",
        "moments",
        "multiplayer",
        "obby",
        "parkour",
        "quest",
        "reaction",
        "scary",
        "secret",
        "speedrun",
        "survival",
        "update",
        "walkthrough",
    }

    useful_phrases = {
        "boss battle",
        "boss fight",
        "funny moments",
        "gameplay highlights",
        "horror gameplay",
        "jump scare",
        "secret ending",
        "survival challenge",
    }

    game_words = {
        word.casefold()
        for word in re.findall(r"[A-Za-z0-9]+", game_name)
    }

    term_counts: dict[str, int] = {}
    phrase_counts: dict[str, int] = {}

    for result in results:
        combined_text = f"{result.title} {result.summary}".casefold()
        words = re.findall(
            r"\b[a-z][a-z0-9'-]{2,}\b",
            combined_text,
        )

        filtered_words = [
            word
            for word in words
            if word not in game_words
        ]

        for word in filtered_words:
            if word not in gaming_vocabulary:
                continue

            term_counts[word] = term_counts.get(word, 0) + 1

        for first_word, second_word in zip(
            filtered_words,
            filtered_words[1:],
        ):
            phrase = f"{first_word} {second_word}"

            if phrase not in useful_phrases:
                continue

            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

    ranked_phrases = sorted(
        phrase_counts,
        key=lambda phrase: (
            -phrase_counts[phrase],
            phrase,
        ),
    )

    ranked_terms = sorted(
        term_counts,
        key=lambda term: (
            -term_counts[term],
            term,
        ),
    )

    selected: list[str] = []
    seen: set[str] = set()

    for value in [*ranked_phrases, *ranked_terms]:
        normalized = value.casefold()

        if normalized in seen:
            continue

        seen.add(normalized)
        selected.append(value.title())

        if len(selected) >= maximum_terms:
            break

    if selected:
        return tuple(selected)

    return (
        "Gameplay",
        "Gaming",
        "Highlights",
        "Reaction",
    )


def _deduplicate_terms(
    terms: Iterable[str],
) -> tuple[str, ...]:
    """Remove empty and duplicate terminology values."""

    result: list[str] = []
    seen: set[str] = set()

    for term in terms:
        cleaned = _clean_text(term)

        if not cleaned:
            continue

        normalized = cleaned.casefold()

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(cleaned)

    return tuple(result)


def _is_authoritative_domain(domain: str) -> bool:
    """Identify common canonical game-information domains."""

    authoritative_fragments = (
        "roblox.com",
        "steampowered.com",
        "playstation.com",
        "xbox.com",
        "nintendo.com",
        "epicgames.com",
        "ea.com",
        "ubisoft.com",
        "rockstargames.com",
        "minecraft.net",
        "wikipedia.org",
    )

    return any(
        fragment in domain
        for fragment in authoritative_fragments
    )


def _extract_domain(url: str) -> str:
    """Extract a lowercase hostname from a URL."""

    try:
        parsed = urlparse(url)
    except ValueError:
        return ""

    return parsed.netloc.casefold().removeprefix("www.")


def _title_case_game_name(value: str) -> str:
    """Apply readable title casing."""

    return " ".join(
        word
        if word.isupper() and len(word) <= 5
        else word.capitalize()
        for word in value.split()
    )


def _normalize_for_comparison(value: str) -> str:
    """Normalize text for fuzzy comparison."""

    return re.sub(
        r"[^a-z0-9]+",
        "",
        value.casefold(),
    )


def _clean_text(value: str) -> str:
    """Normalize whitespace."""

    return " ".join(value.strip().split())