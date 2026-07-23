"""Find candidate gameplay moments using FFmpeg scene detection."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.thumbnail_generator.models.video_request import VideoMode
from src.thumbnail_generator.services.video_analysis_service import (
    VideoMetadata,
)


class MomentScannerError(RuntimeError):
    """Raised when candidate gameplay moments cannot be detected."""


@dataclass(frozen=True, slots=True)
class MomentCandidate:
    """One candidate timestamp for thumbnail frame extraction."""

    timestamp_seconds: float
    source: str
    sequence: int

    @property
    def timestamp_text(self) -> str:
        """Return the timestamp in HH:MM:SS.mmm format."""

        milliseconds = round(self.timestamp_seconds * 1000)
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, milliseconds = divmod(remainder, 1_000)

        return (
            f"{hours:02d}:{minutes:02d}:{seconds:02d}."
            f"{milliseconds:03d}"
        )


_SCENE_TIMESTAMP_PATTERN = re.compile(
    r"pts_time:(?P<timestamp>\d+(?:\.\d+)?)"
)


def scan_candidate_moments(
    video_path: Path,
    metadata: VideoMetadata,
    video_mode: VideoMode,
    candidate_count: int = 5,
) -> list[MomentCandidate]:
    """Find varied candidate moments from one video."""

    if candidate_count < 1:
        raise MomentScannerError(
            "Candidate count must be at least one."
        )

    normalized_path = video_path.expanduser().resolve()

    if not normalized_path.exists() or not normalized_path.is_file():
        raise MomentScannerError(
            f"Video file was not found: {normalized_path}"
        )

    if metadata.duration_seconds <= 0:
        raise MomentScannerError(
            "Video duration must be greater than zero."
        )

    scene_threshold = _get_scene_threshold(video_mode)
    minimum_spacing = _get_minimum_spacing(
        metadata.duration_seconds,
        candidate_count,
        video_mode,
    )
    edge_margin = _get_edge_margin(metadata.duration_seconds)

    detected_timestamps = _detect_scene_timestamps(
        normalized_path,
        scene_threshold,
    )

    filtered_timestamps = _filter_timestamps(
        timestamps=detected_timestamps,
        duration_seconds=metadata.duration_seconds,
        edge_margin=edge_margin,
        minimum_spacing=minimum_spacing,
    )

    selected_timestamps = _select_diverse_timestamps(
        filtered_timestamps,
        candidate_count,
    )

    if len(selected_timestamps) < candidate_count:
        fallback_timestamps = _create_fallback_timestamps(
            duration_seconds=metadata.duration_seconds,
            candidate_count=candidate_count,
            edge_margin=edge_margin,
        )

        selected_timestamps = _merge_timestamps(
            primary=selected_timestamps,
            fallback=fallback_timestamps,
            candidate_count=candidate_count,
            minimum_spacing=minimum_spacing,
        )

    if not selected_timestamps:
        raise MomentScannerError(
            "No usable gameplay moments could be found."
        )

    selected_timestamps.sort()

    return [
        MomentCandidate(
            timestamp_seconds=timestamp,
            source=(
                "scene_detection"
                if _matches_detected_timestamp(
                    timestamp,
                    filtered_timestamps,
                )
                else "uniform_fallback"
            ),
            sequence=index,
        )
        for index, timestamp in enumerate(
            selected_timestamps,
            start=1,
        )
    ]


def _detect_scene_timestamps(
    video_path: Path,
    scene_threshold: float,
) -> list[float]:
    """Run FFmpeg scene detection and return discovered timestamps."""

    filter_expression = (
        f"select='gt(scene,{scene_threshold})',showinfo"
    )

    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-i",
        str(video_path),
        "-an",
        "-vf",
        filter_expression,
        "-fps_mode",
        "vfr",
        "-f",
        "null",
        "-",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as error:
        raise MomentScannerError(
            "FFmpeg was not found. Ensure it is installed and in PATH."
        ) from error
    except OSError as error:
        raise MomentScannerError(
            f"Unable to start FFmpeg: {error}"
        ) from error

    if result.returncode != 0:
        message = result.stderr.strip() or "Unknown FFmpeg error."
        raise MomentScannerError(
            f"Scene detection failed: {message}"
        )

    return [
        float(match.group("timestamp"))
        for match in _SCENE_TIMESTAMP_PATTERN.finditer(result.stderr)
    ]


def _filter_timestamps(
    timestamps: list[float],
    duration_seconds: float,
    edge_margin: float,
    minimum_spacing: float,
) -> list[float]:
    """Remove unsafe, duplicate, and tightly grouped timestamps."""

    usable_start = edge_margin
    usable_end = max(usable_start, duration_seconds - edge_margin)

    sorted_timestamps = sorted(
        timestamp
        for timestamp in timestamps
        if usable_start <= timestamp <= usable_end
    )

    filtered: list[float] = []

    for timestamp in sorted_timestamps:
        if not filtered:
            filtered.append(timestamp)
            continue

        if timestamp - filtered[-1] >= minimum_spacing:
            filtered.append(timestamp)

    return filtered


def _select_diverse_timestamps(
    timestamps: list[float],
    candidate_count: int,
) -> list[float]:
    """Select timestamps distributed across the available scenes."""

    if len(timestamps) <= candidate_count:
        return list(timestamps)

    if candidate_count == 1:
        return [timestamps[len(timestamps) // 2]]

    last_index = len(timestamps) - 1
    selected_indices = {
        round(index * last_index / (candidate_count - 1))
        for index in range(candidate_count)
    }

    return [
        timestamps[index]
        for index in sorted(selected_indices)
    ]


def _create_fallback_timestamps(
    duration_seconds: float,
    candidate_count: int,
    edge_margin: float,
) -> list[float]:
    """Create evenly spaced timestamps inside safe video boundaries."""

    usable_start = edge_margin
    usable_end = max(usable_start, duration_seconds - edge_margin)

    if candidate_count == 1:
        return [(usable_start + usable_end) / 2]

    interval = (usable_end - usable_start) / (candidate_count + 1)

    return [
        usable_start + interval * index
        for index in range(1, candidate_count + 1)
    ]


def _merge_timestamps(
    primary: list[float],
    fallback: list[float],
    candidate_count: int,
    minimum_spacing: float,
) -> list[float]:
    """Fill missing candidates while preserving timestamp spacing."""

    merged = list(primary)

    for timestamp in fallback:
        if len(merged) >= candidate_count:
            break

        if all(
            abs(timestamp - existing) >= minimum_spacing
            for existing in merged
        ):
            merged.append(timestamp)

    if len(merged) < candidate_count:
        for timestamp in fallback:
            if len(merged) >= candidate_count:
                break

            if timestamp not in merged:
                merged.append(timestamp)

    return merged[:candidate_count]


def _matches_detected_timestamp(
    timestamp: float,
    detected_timestamps: list[float],
) -> bool:
    """Check whether a selected timestamp came from scene detection."""

    return any(
        abs(timestamp - detected) < 0.001
        for detected in detected_timestamps
    )


def _get_scene_threshold(video_mode: VideoMode) -> float:
    """Return a scene threshold suited to the video mode."""

    if video_mode is VideoMode.EXISTING_HIGHLIGHT:
        return 0.28

    return 0.35


def _get_minimum_spacing(
    duration_seconds: float,
    candidate_count: int,
    video_mode: VideoMode,
) -> float:
    """Calculate minimum spacing between selected candidates."""

    baseline = duration_seconds / max(candidate_count * 4, 1)

    if video_mode is VideoMode.EXISTING_HIGHLIGHT:
        return max(2.0, min(baseline, 12.0))

    return max(8.0, min(baseline, 45.0))


def _get_edge_margin(duration_seconds: float) -> float:
    """Avoid title cards and end screens near video boundaries."""

    return max(1.0, min(duration_seconds * 0.03, 20.0))