from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class VisualReasoning:
    """Visual AI analysis of a generated gaming highlight."""

    rank: int

    visual_event: str
    action_level: str
    danger_level: str

    looks_interesting: bool
    reason: str
    confidence: float