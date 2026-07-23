"""Analyze video metadata with ffprobe."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class VideoAnalysisError(RuntimeError):
    """Raised when video metadata cannot be analyzed."""


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """Metadata extracted from one video file."""

    path: Path
    duration_seconds: float
    width: int
    height: int
    frame_rate: float
    video_codec: str
    has_audio: bool

    @property
    def duration_text(self) -> str:
        """Return duration in HH:MM:SS format."""

        total_seconds = max(0, round(self.duration_seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def resolution_text(self) -> str:
        """Return resolution in WIDTHxHEIGHT format."""

        return f"{self.width}x{self.height}"


def analyze_video(video_path: Path) -> VideoMetadata:
    """Analyze one video file using ffprobe."""

    normalized_path = video_path.expanduser().resolve()

    if not normalized_path.exists():
        raise VideoAnalysisError(
            f"Video file was not found: {normalized_path}"
        )

    if not normalized_path.is_file():
        raise VideoAnalysisError(
            f"Video path is not a file: {normalized_path}"
        )

    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(normalized_path),
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
        raise VideoAnalysisError(
            "ffprobe was not found. Install FFmpeg and ensure it is in PATH."
        ) from error
    except OSError as error:
        raise VideoAnalysisError(
            f"Unable to start ffprobe: {error}"
        ) from error

    if result.returncode != 0:
        message = result.stderr.strip() or "Unknown ffprobe error."
        raise VideoAnalysisError(
            f"ffprobe failed for '{normalized_path}': {message}"
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise VideoAnalysisError(
            "ffprobe returned invalid JSON output."
        ) from error

    return _parse_metadata(normalized_path, payload)


def _parse_metadata(
    video_path: Path,
    payload: dict[str, Any],
) -> VideoMetadata:
    """Convert ffprobe JSON into validated video metadata."""

    streams = payload.get("streams")
    format_data = payload.get("format")

    if not isinstance(streams, list):
        raise VideoAnalysisError(
            "ffprobe output does not contain a valid streams list."
        )

    if not isinstance(format_data, dict):
        raise VideoAnalysisError(
            "ffprobe output does not contain valid format metadata."
        )

    video_stream = next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict)
            and stream.get("codec_type") == "video"
        ),
        None,
    )

    if video_stream is None:
        raise VideoAnalysisError(
            f"No video stream was found in: {video_path}"
        )

    audio_stream = next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict)
            and stream.get("codec_type") == "audio"
        ),
        None,
    )

    duration_seconds = _parse_float(format_data.get("duration"))
    width = _parse_int(video_stream.get("width"))
    height = _parse_int(video_stream.get("height"))
    frame_rate = _parse_frame_rate(
        video_stream.get("avg_frame_rate")
        or video_stream.get("r_frame_rate")
    )
    video_codec = str(
        video_stream.get("codec_name") or "unknown"
    )

    if duration_seconds <= 0:
        raise VideoAnalysisError(
            f"Invalid video duration reported for: {video_path}"
        )

    if width <= 0 or height <= 0:
        raise VideoAnalysisError(
            f"Invalid video resolution reported for: {video_path}"
        )

    return VideoMetadata(
        path=video_path,
        duration_seconds=duration_seconds,
        width=width,
        height=height,
        frame_rate=frame_rate,
        video_codec=video_codec,
        has_audio=audio_stream is not None,
    )


def _parse_float(value: Any) -> float:
    """Convert a value to float safely."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_int(value: Any) -> int:
    """Convert a value to int safely."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_frame_rate(value: Any) -> float:
    """Convert an ffprobe frame-rate fraction to float."""

    if not isinstance(value, str) or not value:
        return 0.0

    if "/" not in value:
        return _parse_float(value)

    numerator_text, denominator_text = value.split("/", maxsplit=1)
    numerator = _parse_float(numerator_text)
    denominator = _parse_float(denominator_text)

    if denominator == 0:
        return 0.0

    return numerator / denominator