from dataclasses import dataclass

from src.models.asr_segment import ASRSegment
from src.models.scene import Scene


@dataclass(slots=True, frozen=True)
class SceneAnalysis:
    """Scene with speech segments that overlap its timeline."""

    scene: Scene
    transcript_segments: list[ASRSegment]

    @property
    def transcript_text(self) -> str:
        return " ".join(
            segment.text
            for segment in self.transcript_segments
            if segment.text
        )