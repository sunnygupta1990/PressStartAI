from dataclasses import dataclass

from src.models.final_highlight import FinalHighlight


@dataclass(slots=True, frozen=True)
class RenderedShort:
    """A rendered vertical Short created from an approved highlight."""

    file_path: str
    highlight: FinalHighlight
    width: int
    height: int

    @property
    def rank(self) -> int:
        return self.highlight.rank

    @property
    def duration_seconds(self) -> float:
        return self.highlight.duration_seconds

    @property
    def category(self) -> str:
        return self.highlight.category

    @property
    def confidence(self) -> float:
        return self.highlight.confidence