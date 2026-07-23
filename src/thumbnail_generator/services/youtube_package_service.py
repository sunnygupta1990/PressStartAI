"""Generate upload-ready YouTube metadata packages."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import re
from typing import Any, Sequence

from src.thumbnail_generator.models.video_request import VideoRequest
from src.thumbnail_generator.services.internet_research_service import (
    GameResearch,
)

class YouTubePackageError(RuntimeError):
    """Raised when YouTube metadata cannot be generated or saved."""


@dataclass(frozen=True, slots=True)
class YouTubePackage:
    """Upload-ready YouTube metadata for one video."""

    profile_key: str
    channel_name: str
    game_name: str
    video_type: str
    episode_topic: str
    preferred_language: str
    primary_title: str
    alternate_titles: tuple[str, ...]
    description: str
    hashtags: tuple[str, ...]
    tags: tuple[str, ...]
    source_video: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable package data."""

        data = asdict(self)
        data["alternate_titles"] = list(self.alternate_titles)
        data["hashtags"] = list(self.hashtags)
        data["tags"] = list(self.tags)
        return data


@dataclass(frozen=True, slots=True)
class SavedYouTubePackage:
    """Paths created for one YouTube metadata package."""

    package: YouTubePackage
    text_path: Path
    json_path: Path


def generate_youtube_package(
    request: VideoRequest,
    profile: dict[str, Any],
    research: GameResearch | None = None,
) -> YouTubePackage:
    """Generate upload-ready metadata using researched game context."""

    effective_request = request

    if research is not None and research.effective_game_name:
        effective_request = replace(
            request,
            game_name=research.effective_game_name,
        )

    preferred_language = str(
        profile.get("preferred_language", "English")
    ).strip()

    primary_title, alternate_titles = _build_titles(
        request=effective_request,
        preferred_language=preferred_language,
    )

    description = _build_description(
        request=effective_request,
        profile=profile,
    )

    hashtags = _build_hashtags(effective_request)
    tags = _build_tags(effective_request, profile)

    return YouTubePackage(
        profile_key=effective_request.profile_key,
        channel_name=effective_request.channel_name,
        game_name=effective_request.game_name,
        video_type=effective_request.video_type,
        episode_topic=effective_request.episode_topic,
        preferred_language=preferred_language,
        primary_title=primary_title,
        alternate_titles=alternate_titles,
        description=description,
        hashtags=hashtags,
        tags=tags,
        source_video=str(effective_request.video_path),
    )


def save_youtube_package(
    package: YouTubePackage,
    output_directory: Path,
) -> SavedYouTubePackage:
    """Save YouTube metadata as TXT and JSON files."""

    normalized_directory = output_directory.expanduser().resolve()

    try:
        normalized_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as error:
        raise YouTubePackageError(
            f"Unable to create YouTube package folder: {error}"
        ) from error

    text_path = normalized_directory / "youtube_package.txt"
    json_path = normalized_directory / "youtube_package.json"

    try:
        text_path.write_text(
            _render_text_package(package),
            encoding="utf-8",
        )

        json_path.write_text(
            json.dumps(
                package.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError as error:
        raise YouTubePackageError(
            f"Unable to save YouTube package: {error}"
        ) from error

    _validate_saved_file(text_path)
    _validate_saved_file(json_path)

    return SavedYouTubePackage(
        package=package,
        text_path=text_path,
        json_path=json_path,
    )


def _build_titles(
    request: VideoRequest,
    preferred_language: str,
) -> tuple[str, tuple[str, ...]]:
    """Create one primary title and four alternatives."""

    game_name = _clean_text(request.game_name)
    video_type = _clean_text(request.video_type)
    episode_topic = _clean_text(request.episode_topic)

    language = preferred_language.lower()
    video_type_lower = video_type.lower()

    if "funny" in video_type_lower:
        title_templates = (
            f"{game_name} Mein Sab Ulta Ho Gaya! | {episode_topic}",
            f"Biggest {game_name} Fail Ever! | {episode_topic}",
            f"{game_name} Gone Wrong 😂 | {episode_topic}",
            f"Control Hi Nahi Hua! {game_name} Funny Moments",
            f"{episode_topic}: The Funniest {game_name} Gameplay",
        )
    elif "challenge" in video_type_lower:
        title_templates = (
            f"Can I Complete This {game_name} Challenge? | {episode_topic}",
            f"This {game_name} Challenge Felt Impossible!",
            f"Last Try Clutch in {game_name} | {episode_topic}",
            f"{game_name} Challenge Accepted!",
            f"Did I Complete the Challenge? | {episode_topic}",
        )
    elif "walkthrough" in video_type_lower:
        title_templates = (
            f"{game_name} Walkthrough | {episode_topic}",
            f"{episode_topic} Begins! | {game_name} Gameplay",
            f"Secret Path Found in {game_name} | {episode_topic}",
            f"{game_name} Full Gameplay Walkthrough",
            f"Exploring {episode_topic} in {game_name}",
        )
    elif "boss" in video_type_lower:
        title_templates = (
            f"{game_name} Boss Fight | {episode_topic}",
            f"This Boss Was Too Powerful! | {game_name}",
            f"One Last Attempt Against the Boss",
            f"Did I Beat the Boss? | {game_name}",
            f"Final Clutch Boss Fight | {episode_topic}",
        )
    else:
        title_templates = (
            f"{game_name} Gameplay | {episode_topic}",
            f"This Changed Everything in {game_name}",
            f"The Most Dangerous Moment in {game_name}",
            f"{episode_topic} Starts Now! | {game_name}",
            f"{game_name} Full Action Gameplay",
        )

    if "english" in language and "hinglish" not in language:
        title_templates = tuple(
            _convert_title_to_english(title)
            for title in title_templates
        )

    normalized_titles = tuple(
        _limit_title_length(title)
        for title in title_templates
    )

    return normalized_titles[0], normalized_titles[1:]


def _build_description(
    request: VideoRequest,
    profile: dict[str, Any],
) -> str:
    """Create an SEO-focused video description."""

    audience = _clean_text(
        str(profile.get("target_audience", "gaming viewers"))
    )
    game_name = _clean_text(request.game_name)
    video_type = _clean_text(request.video_type)
    episode_topic = _clean_text(request.episode_topic)

    lines = [
        (
            f"Welcome to {request.channel_name}! In this video, "
            f"we play {game_name} and take on {episode_topic}."
        ),
        "",
        (
            f"This is a {video_type} gameplay video created for "
            f"{audience}."
        ),
        "",
        (
            f"Watch till the end for the strongest moments, reactions, "
            f"fails, action, and surprises from this {game_name} session."
        ),
        "",
        "Subscribe for more gaming videos, challenges, walkthroughs, "
        "funny moments, and highlights.",
        "",
        "Video details:",
        f"Game: {game_name}",
        f"Video type: {video_type}",
        f"Episode/topic: {episode_topic}",
        f"Channel: {request.channel_name}",
        "",
        "Hashtags:",
        " ".join(_build_hashtags(request)),
    ]

    return "\n".join(lines)


def _build_hashtags(
    request: VideoRequest,
) -> tuple[str, ...]:
    """Create concise hashtags for the video."""

    game_tag = _hashtag(request.game_name)
    video_type_tag = _hashtag(request.video_type)

    hashtags = [
        game_tag,
        "#Gaming",
        "#Gameplay",
        video_type_tag,
        "#GamingVideo",
    ]

    return _deduplicate(hashtags)


def _build_tags(
    request: VideoRequest,
    profile: dict[str, Any],
) -> tuple[str, ...]:
    """Create searchable YouTube tags and keywords."""

    game_name = _clean_text(request.game_name)
    video_type = _clean_text(request.video_type)
    episode_topic = _clean_text(request.episode_topic)
    language = _clean_text(
        str(profile.get("preferred_language", "English"))
    )

    tags = [
        game_name,
        f"{game_name} gameplay",
        f"{game_name} {video_type}",
        f"{game_name} {episode_topic}",
        video_type,
        episode_topic,
        "gaming",
        "gameplay",
        "gaming video",
        "gameplay highlights",
        f"{language} gaming",
        request.channel_name,
    ]

    return _deduplicate(tags)


def _render_text_package(
    package: YouTubePackage,
) -> str:
    """Render a human-readable YouTube package."""

    alternate_titles = "\n".join(
        f"{index}. {title}"
        for index, title in enumerate(
            package.alternate_titles,
            start=1,
        )
    )

    return (
        "YOUTUBE UPLOAD PACKAGE\n"
        "======================\n\n"
        f"Channel: {package.channel_name}\n"
        f"Profile: {package.profile_key}\n"
        f"Game: {package.game_name}\n"
        f"Video type: {package.video_type}\n"
        f"Episode/topic: {package.episode_topic}\n"
        f"Language: {package.preferred_language}\n"
        f"Source video: {package.source_video}\n\n"
        "PRIMARY TITLE\n"
        "-------------\n"
        f"{package.primary_title}\n\n"
        "ALTERNATE TITLES\n"
        "----------------\n"
        f"{alternate_titles}\n\n"
        "DESCRIPTION\n"
        "-----------\n"
        f"{package.description}\n\n"
        "HASHTAGS\n"
        "--------\n"
        f"{' '.join(package.hashtags)}\n\n"
        "TAGS / KEYWORDS\n"
        "---------------\n"
        f"{', '.join(package.tags)}\n"
    )


def _convert_title_to_english(title: str) -> str:
    """Convert common Hinglish title phrases to English."""

    replacements = {
        "Mein Sab Ulta Ho Gaya!": "Everything Went Wrong!",
        "Control Hi Nahi Hua!": "I Lost Control!",
    }

    converted = title

    for source, replacement in replacements.items():
        converted = converted.replace(source, replacement)

    return converted


def _limit_title_length(
    title: str,
    maximum_length: int = 100,
) -> str:
    """Keep a title inside YouTube's practical title limit."""

    cleaned = _clean_text(title)

    if len(cleaned) <= maximum_length:
        return cleaned

    shortened = cleaned[: maximum_length - 3].rstrip()

    if " " in shortened:
        shortened = shortened.rsplit(" ", maxsplit=1)[0]

    return f"{shortened}..."


def _clean_text(value: str) -> str:
    """Normalize whitespace in user-provided text."""

    return " ".join(value.strip().split())


def _hashtag(value: str) -> str:
    """Convert text into a hashtag."""

    cleaned = re.sub(
        r"[^a-zA-Z0-9]+",
        "",
        value,
    )

    return f"#{cleaned}" if cleaned else "#Gaming"


def _deduplicate(
    values: Sequence[str],
) -> tuple[str, ...]:
    """Remove duplicates while preserving order."""

    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        normalized = value.casefold()

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(value)

    return tuple(result)


def _validate_saved_file(path: Path) -> None:
    """Validate one saved metadata file."""

    if not path.exists():
        raise YouTubePackageError(
            f"Expected package file was not created: {path}"
        )

    if path.stat().st_size == 0:
        path.unlink(missing_ok=True)
        raise YouTubePackageError(
            f"Package file is empty: {path}"
        )