from dataclasses import dataclass

from src.models.rendered_short import RenderedShort
from src.models.short_metadata import ShortMetadata


@dataclass(slots=True, frozen=True)
class ShortPackage:
    """Complete ready-to-publish package for one YouTube Short."""

    rendered_short: RenderedShort
    final_video_file: str
    subtitle_file: str
    metadata: ShortMetadata

    @property
    def rank(self) -> int:
        return self.rendered_short.rank

    @property
    def category(self) -> str:
        return self.rendered_short.category

    @property
    def confidence(self) -> float:
        return self.rendered_short.confidence