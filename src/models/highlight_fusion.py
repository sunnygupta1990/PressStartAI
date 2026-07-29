from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class HighlightFusion:
    """Final multimodal AI decision for one gaming highlight."""

    rank: int

    keep_highlight: bool

    category: str
    event_summary: str

    commentary_category: str
    visual_event: str

    action_level: str
    danger_level: str

    final_confidence: float
    reason: str