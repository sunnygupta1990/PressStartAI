"""Score extracted gameplay frames for thumbnail suitability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from src.thumbnail_generator.services.frame_extraction_service import (
    ExtractedFrame,
)


class FrameScoringError(RuntimeError):
    """Raised when extracted frames cannot be scored."""


@dataclass(frozen=True, slots=True)
class FrameScore:
    """Visual-quality score for one extracted gameplay frame."""

    frame: ExtractedFrame
    total_score: float
    brightness_score: float
    contrast_score: float
    sharpness_score: float
    color_score: float
    detail_score: float
    rank: int = 0

    @property
    def image_path(self) -> Path:
        """Return the scored image path."""

        return self.frame.image_path

    @property
    def timestamp_text(self) -> str:
        """Return the source timestamp."""

        return self.frame.timestamp_text


def score_extracted_frames(
    frames: list[ExtractedFrame],
) -> list[FrameScore]:
    """Score and rank extracted frames from strongest to weakest."""

    if not frames:
        raise FrameScoringError(
            "At least one extracted frame is required."
        )

    scored_frames = [
        _score_single_frame(frame)
        for frame in frames
    ]

    ranked_frames = sorted(
        scored_frames,
        key=lambda item: item.total_score,
        reverse=True,
    )

    return [
        FrameScore(
            frame=item.frame,
            total_score=item.total_score,
            brightness_score=item.brightness_score,
            contrast_score=item.contrast_score,
            sharpness_score=item.sharpness_score,
            color_score=item.color_score,
            detail_score=item.detail_score,
            rank=index,
        )
        for index, item in enumerate(ranked_frames, start=1)
    ]


def _score_single_frame(frame: ExtractedFrame) -> FrameScore:
    """Calculate visual metrics for one frame."""

    image = _load_image(frame.image_path)

    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mean_brightness = float(np.mean(grayscale))
    contrast_value = float(np.std(grayscale))
    sharpness_value = float(
        cv2.Laplacian(grayscale, cv2.CV_64F).var()
    )
    saturation_value = float(np.mean(hsv_image[:, :, 1]))
    detail_value = _calculate_edge_density(grayscale)

    brightness_score = _score_brightness(mean_brightness)
    contrast_score = _scale_score(
        contrast_value,
        minimum=20.0,
        maximum=75.0,
    )
    sharpness_score = _scale_score(
        sharpness_value,
        minimum=30.0,
        maximum=900.0,
    )
    color_score = _scale_score(
        saturation_value,
        minimum=25.0,
        maximum=150.0,
    )
    detail_score = _scale_score(
        detail_value,
        minimum=0.02,
        maximum=0.22,
    )

    total_score = (
        brightness_score * 0.20
        + contrast_score * 0.20
        + sharpness_score * 0.30
        + color_score * 0.15
        + detail_score * 0.15
    )

    return FrameScore(
        frame=frame,
        total_score=round(total_score, 2),
        brightness_score=round(brightness_score, 2),
        contrast_score=round(contrast_score, 2),
        sharpness_score=round(sharpness_score, 2),
        color_score=round(color_score, 2),
        detail_score=round(detail_score, 2),
    )


def _load_image(image_path: Path) -> np.ndarray:
    """Load one frame and validate its image data."""

    normalized_path = image_path.expanduser().resolve()

    if not normalized_path.exists():
        raise FrameScoringError(
            f"Extracted frame was not found: {normalized_path}"
        )

    if not normalized_path.is_file():
        raise FrameScoringError(
            f"Extracted frame path is not a file: {normalized_path}"
        )

    image = cv2.imread(str(normalized_path), cv2.IMREAD_COLOR)

    if image is None:
        raise FrameScoringError(
            f"Unable to read extracted frame: {normalized_path}"
        )

    if image.size == 0:
        raise FrameScoringError(
            f"Extracted frame is empty: {normalized_path}"
        )

    return image


def _score_brightness(mean_brightness: float) -> float:
    """Reward balanced brightness and penalize extreme exposure."""

    ideal_brightness = 130.0
    maximum_distance = 125.0

    distance = abs(mean_brightness - ideal_brightness)
    score = 100.0 * (1.0 - distance / maximum_distance)

    return _clamp_score(score)


def _calculate_edge_density(grayscale: np.ndarray) -> float:
    """Measure visible structural detail using edge density."""

    edges = cv2.Canny(
        grayscale,
        threshold1=80,
        threshold2=160,
    )

    edge_pixels = int(np.count_nonzero(edges))
    total_pixels = int(edges.size)

    if total_pixels == 0:
        return 0.0

    return edge_pixels / total_pixels


def _scale_score(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Scale one metric into a normalized 0–100 score."""

    if maximum <= minimum:
        raise FrameScoringError(
            "Score maximum must be greater than minimum."
        )

    normalized = (value - minimum) / (maximum - minimum)
    return _clamp_score(normalized * 100.0)


def _clamp_score(value: float) -> float:
    """Restrict one score to the inclusive 0–100 range."""

    return max(0.0, min(value, 100.0))