import subprocess
from pathlib import Path

from src.models.final_highlight import FinalHighlight
from src.models.rendered_short import RenderedShort


class ShortRenderer:
    """Render approved highlights as vertical 9:16 Shorts."""

    OUTPUT_WIDTH = 1080
    OUTPUT_HEIGHT = 1920

    def render(
        self,
        highlight: FinalHighlight,
        output_folder: str,
    ) -> RenderedShort:
        source_path = Path(
            highlight.file_path
        )

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Highlight video does not exist: "
                f"{source_path}"
            )

        output_path = Path(
            output_folder
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = output_path / (
            f"short_{highlight.rank:03d}.mp4"
        )

        video_filter = (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output_file),
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode != 0:
            raise RuntimeError(
                "FFmpeg failed to render vertical Short: "
                f"{process.stderr}"
            )

        if not output_file.is_file():
            raise RuntimeError(
                "Rendered Short was not created: "
                f"{output_file}"
            )

        return RenderedShort(
            file_path=str(output_file),
            highlight=highlight,
            width=self.OUTPUT_WIDTH,
            height=self.OUTPUT_HEIGHT,
        )