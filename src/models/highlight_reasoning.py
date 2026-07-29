from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class HighlightReasoning:
    """AI reasoning result for one generated highlight."""

    rank: int
    is_interesting: bool
    category: str
    reason: str
    confidence: float