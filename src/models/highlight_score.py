from dataclasses import dataclass

from src.models.highlight_features import HighlightFeatures


@dataclass(slots=True, frozen=True)
class HighlightScore:
    """Score assigned to one highlight candidate."""

    features: HighlightFeatures

    speech_score: float
    motion_score: float
    audio_score: float

    final_score: float