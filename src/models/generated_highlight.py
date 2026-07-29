from dataclasses import dataclass

from src.models.highlight_candidate import HighlightCandidate


@dataclass(slots=True, frozen=True)
class GeneratedHighlight:
    """Generated highlight clip with its source candidate metadata."""

    file_path: str
    candidate: HighlightCandidate

    @property
    def rank(self) -> int:
        return self.candidate.rank

    @property
    def start_seconds(self) -> float:
        return self.candidate.start_seconds

    @property
    def end_seconds(self) -> float:
        return self.candidate.end_seconds

    @property
    def duration_seconds(self) -> float:
        return self.candidate.duration_seconds

    @property
    def final_score(self) -> float:
        return self.candidate.score.final_score

    @property
    def transcript_text(self) -> str:
        return self.candidate.score.features.transcript_text