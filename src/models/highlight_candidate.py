from dataclasses import dataclass

from src.models.highlight_score import HighlightScore


@dataclass(slots=True, frozen=True)
class HighlightCandidate:
    """A ranked video highlight candidate."""

    start_seconds: float
    end_seconds: float
    rank: int
    score: HighlightScore

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds