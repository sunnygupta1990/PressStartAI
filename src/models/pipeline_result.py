from dataclasses import dataclass

from src.models.final_highlight import FinalHighlight
from src.models.pipeline_stage_timing import PipelineStageTiming
from src.models.short_package import ShortPackage


@dataclass(slots=True, frozen=True)
class PipelineResult:
    """Result of one complete PressStartAI pipeline run."""

    source_video_file: str
    video_duration_seconds: float
    final_highlights: list[FinalHighlight]
    exported_files: list[str]
    short_packages: list[ShortPackage]
    stage_timings: list[PipelineStageTiming]

    @property
    def highlight_count(self) -> int:
        return len(self.final_highlights)

    @property
    def exported_file_count(self) -> int:
        return len(self.exported_files)

    @property
    def short_package_count(self) -> int:
        return len(self.short_packages)

    @property
    def total_duration_seconds(self) -> float:
        return sum(
            timing.duration_seconds
            for timing in self.stage_timings
        )