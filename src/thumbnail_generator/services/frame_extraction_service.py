"""Extract thumbnail candidate frames from gameplay videos."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.thumbnail_generator.services.moment_scanner_service import (
    MomentCandidate,
)


class FrameExtractionError(RuntimeError):
    """Raised when candidate frames cannot be extracted."""


@dataclass(frozen=True, slots=True)
class ExtractedFrame:
    """One gameplay frame extracted from a candidate moment."""

    candidate: MomentCandidate
    image_path: Path

    @property
    def timestamp_seconds(self) -> float:
        """Return the source timestamp in seconds."""

        return self.candidate.timestamp_seconds

    @property
    def timestamp_text(self) -> str:
        """Return the formatted source timestamp."""

        return self.candidate.timestamp_text


def extract_candidate_frames(
    video_path: Path,
    candidates: list[MomentCandidate],
    output_directory: Path,
    width: int = 1280,
    height: int = 720,
) -> list[ExtractedFrame]:
    """Extract one image for each candidate gameplay moment."""

    normalized_video_path = video_path.expanduser().resolve()
    normalized_output_directory = output_directory.expanduser().resolve()

    _validate_inputs(
        video_path=normalized_video_path,
        candidates=candidates,
        width=width,
        height=height,
    )

    try:
        normalized_output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as error:
        raise FrameExtractionError(
            f"Unable to create output folder "
            f"'{normalized_output_directory}': {error}"
        ) from error

    extracted_frames: list[ExtractedFrame] = []

    for candidate in candidates:
        output_path = normalized_output_directory / _build_filename(
            candidate
        )

        _extract_single_frame(
            video_path=normalized_video_path,
            candidate=candidate,
            output_path=output_path,
            width=width,
            height=height,
        )

        extracted_frames.append(
            ExtractedFrame(
                candidate=candidate,
                image_path=output_path,
            )
        )

    return extracted_frames


def _extract_single_frame(
    video_path: Path,
    candidate: MomentCandidate,
    output_path: Path,
    width: int,
    height: int,
) -> None:
    """Extract one scaled frame with FFmpeg."""

    scale_filter = (
        f"scale={width}:{height}:"
        "force_original_aspect_ratio=increase,"
        f"crop={width}:{height}"
    )

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-ss",
        f"{candidate.timestamp_seconds:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-vf",
        scale_filter,
        "-q:v",
        "2",
        "-y",
        str(output_path),
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
        raise FrameExtractionError(
            "FFmpeg was not found. Ensure it is installed and in PATH."
        ) from error
    except OSError as error:
        raise FrameExtractionError(
            f"Unable to start FFmpeg: {error}"
        ) from error

    if result.returncode != 0:
        message = result.stderr.strip() or "Unknown FFmpeg error."
        raise FrameExtractionError(
            f"Frame extraction failed at "
            f"{candidate.timestamp_text}: {message}"
        )

    if not output_path.exists():
        raise FrameExtractionError(
            f"FFmpeg did not create the expected frame: {output_path}"
        )

    if output_path.stat().st_size == 0:
        output_path.unlink(missing_ok=True)
        raise FrameExtractionError(
            f"FFmpeg created an empty frame at "
            f"{candidate.timestamp_text}."
        )


def _validate_inputs(
    video_path: Path,
    candidates: list[MomentCandidate],
    width: int,
    height: int,
) -> None:
    """Validate frame extraction inputs."""

    if not video_path.exists():
        raise FrameExtractionError(
            f"Video file was not found: {video_path}"
        )

    if not video_path.is_file():
        raise FrameExtractionError(
            f"Video path is not a file: {video_path}"
        )

    if not candidates:
        raise FrameExtractionError(
            "At least one moment candidate is required."
        )

    if width <= 0 or height <= 0:
        raise FrameExtractionError(
            "Frame width and height must be greater than zero."
        )

    for candidate in candidates:
        if candidate.timestamp_seconds < 0:
            raise FrameExtractionError(
                "Candidate timestamps cannot be negative."
            )


def _build_filename(candidate: MomentCandidate) -> str:
    """Build a descriptive candidate frame filename."""

    timestamp_slug = (
        candidate.timestamp_text
        .replace(":", "-")
        .replace(".", "-")
    )

    return (
        f"candidate_{candidate.sequence:02d}_"
        f"{candidate.source}_"
        f"{timestamp_slug}.jpg"
    )