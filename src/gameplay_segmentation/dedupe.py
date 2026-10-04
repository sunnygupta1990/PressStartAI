from __future__ import annotations

import re

from src.gameplay_segmentation.models import ClipCandidate


def temporal_iou(a: ClipCandidate, b: ClipCandidate) -> float:
    intersection = max(0.0, min(a.end_seconds, b.end_seconds) - max(a.start_seconds, b.start_seconds))
    union = max(a.end_seconds, b.end_seconds) - min(a.start_seconds, b.start_seconds)
    return intersection / union if union > 0 else 0.0


def temporal_overlap_ratio(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    intersection = max(0.0, min(a_end, b_end) - max(a_start, b_start))
    if intersection <= 0:
        return 0.0
    shorter = max(1e-6, min(a_end - a_start, b_end - b_start))
    return intersection / shorter


def semantic_similarity(a: ClipCandidate, b: ClipCandidate) -> float:
    left = _tokens(a.description)
    right = _tokens(b.description)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _tokens(text: str) -> set[str]:
    return {
        x for x in re.findall(r"[a-z0-9]+", str(text).lower())
        if len(x) > 2
    }


def _context_match(a: ClipCandidate, b: ClipCandidate) -> bool:
    category_match = a.category == b.category
    location_match = (
        a.location == b.location
        or a.location == "Unknown"
        or b.location == "Unknown"
    )
    shot_match = a.shot_type == b.shot_type
    return category_match and location_match and shot_match


def remove_redundant(
    candidates: list[ClipCandidate],
    iou_threshold: float = 0.72,
    semantic_threshold: float = 0.55,
) -> list[ClipCandidate]:
    """
    Remove near-identical candidates using temporal and semantic context.

    High temporal overlap with the same context is sufficient to treat clips as
    duplicates even when descriptions use different wording. Meaningful clips
    with only partial overlap remain allowed.
    """
    ordered = sorted(
        candidates,
        key=lambda c: (-c.confidence, c.start_seconds, -(c.end_seconds - c.start_seconds)),
    )
    kept: list[ClipCandidate] = []
    for candidate in ordered:
        duplicate = False
        for existing in kept:
            overlap = temporal_overlap_ratio(
                candidate.start_seconds, candidate.end_seconds,
                existing.start_seconds, existing.end_seconds,
            )
            if overlap >= iou_threshold and _context_match(candidate, existing):
                duplicate = True
                break
            iou = temporal_iou(candidate, existing)
            similarity = semantic_similarity(candidate, existing)
            if iou >= 0.55 and similarity >= semantic_threshold and _context_match(candidate, existing):
                duplicate = True
                break
        if not duplicate:
            kept.append(candidate)
    return sorted(kept, key=lambda c: (c.start_seconds, c.end_seconds))
