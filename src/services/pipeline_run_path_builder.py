from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.models.pipeline_run_paths import PipelineRunPaths


class PipelineRunPathBuilder:
    """Build isolated working and output folders for one pipeline run."""

    def build(
        self,
        video_file: str,
        working_root: str = "temp/runs",
        output_root: str = "output/runs",
    ) -> PipelineRunPaths:
        video_path = Path(video_file)

        safe_video_name = self._make_safe_name(
            video_path.stem
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        unique_suffix = uuid4().hex[:8]

        run_id = (
            f"{timestamp}_"
            f"{safe_video_name}_"
            f"{unique_suffix}"
        )

        working_folder = (
            Path(working_root) / run_id
        )

        output_folder = (
            Path(output_root) / run_id
        )

        return PipelineRunPaths(
            run_id=run_id,
            working_folder=str(working_folder),
            output_folder=str(output_folder),
        )

    @staticmethod
    def _make_safe_name(
        value: str,
    ) -> str:
        safe_characters = [
            character
            if character.isalnum()
            else "_"
            for character in value
        ]

        safe_name = "".join(
            safe_characters
        ).strip("_")

        if not safe_name:
            return "video"

        return safe_name