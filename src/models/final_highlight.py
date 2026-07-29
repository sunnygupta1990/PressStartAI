from dataclasses import dataclass

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_fusion import HighlightFusion


@dataclass(slots=True, frozen=True)
class FinalHighlight:
    """Final AI-approved highlight with its generated video clip."""

    highlight: GeneratedHighlight
    fusion: HighlightFusion

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
    def transcript_text(self) -> str:
        return self.highlight.transcript_text

    @property
    def heuristic_score(self) -> float:
        return self.highlight.final_score

    @property
    def category(self) -> str:
        return self.fusion.category

    @property
    def event_summary(self) -> str:
        return self.fusion.event_summary

    @property
    def commentary_category(self) -> str:
        return self.fusion.commentary_category

    @property
    def visual_event(self) -> str:
        return self.fusion.visual_event

    @property
    def action_level(self) -> str:
        return self.fusion.action_level

    @property
    def danger_level(self) -> str:
        return self.fusion.danger_level

    @property
    def confidence(self) -> float:
        return self.fusion.final_confidence

    @property
    def reason(self) -> str:
        return self.fusion.reason