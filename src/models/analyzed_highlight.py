from dataclasses import dataclass

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_reasoning import HighlightReasoning


@dataclass(slots=True, frozen=True)
class AnalyzedHighlight:
    """Generated highlight combined with local AI reasoning."""

    highlight: GeneratedHighlight
    reasoning: HighlightReasoning

    @property
    def file_path(self) -> str:
        return self.highlight.file_path

    @property
    def rank(self) -> int:
        return self.highlight.rank

    @property
    def start_seconds(self) -> float:
        return self.highlight.start_seconds

    @property
    def end_seconds(self) -> float:
        return self.highlight.end_seconds

    @property
    def duration_seconds(self) -> float:
        return self.highlight.duration_seconds

    @property
    def final_score(self) -> float:
        return self.highlight.final_score

    @property
    def transcript_text(self) -> str:
        return self.highlight.transcript_text

    @property
    def is_interesting(self) -> bool:
        return self.reasoning.is_interesting

    @property
    def category(self) -> str:
        return self.reasoning.category

    @property
    def reason(self) -> str:
        return self.reasoning.reason

    @property
    def confidence(self) -> float:
        return self.reasoning.confidence