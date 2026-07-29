# src/services/short_renderer.py

"""Render approved highlights as vertical Shorts without aspect-ratio distortion."""

from __future__ import annotations

from pathlib import Path
import subprocess

from src.models.final_highlight import FinalHighlight
from src.models.rendered_short import RenderedShort


class ShortRenderer:
    """Render a centered source video over a blurred vertical background."""

    OUTPUT_WIDTH = 1080
    OUTPUT_HEIGHT = 1920
    FOREGROUND_HEIGHT = 576

    def render(
        self,
        highlight: FinalHighlight,
        output_folder: str,
    ) -> RenderedShort:
        """Render one distortion-free 9:16 Short."""

        source_path = Path(highlight.file_path).expanduser().resolve()

        if not source_path.is_file():
            raise FileNotFoundError(
                f"Highlight video does not exist: {source_path}"
            )

        output_path = Path(output_folder).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / f"short_{highlight.rank:03d}.mp4"

        filter_complex = (
            "[0:v]split=2[background_source][foreground_source];"
            "[background_source]"
            f"scale={self.OUTPUT_WIDTH}:{self.OUTPUT_HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={self.OUTPUT_WIDTH}:{self.OUTPUT_HEIGHT},"
            "gblur=sigma=32:steps=2,"
            "setsar=1"
            "[background];"
            "[foreground_source]"
            f"scale={self.OUTPUT_WIDTH}:{self.FOREGROUND_HEIGHT}:"
            "force_original_aspect_ratio=decrease,"
            "setsar=1"
            "[foreground];"
            "[background][foreground]"
            "overlay=(W-w)/2:(H-h)/2:"
            "format=auto,"
            "setsar=1"
            "[video]"
        )

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "[video]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
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
                "FFmpeg failed to render the vertical Short:\n"
                f"{process.stderr.strip()}"
            )

        if not output_file.is_file() or output_file.stat().st_size == 0:
            raise RuntimeError(
                f"Rendered Short was not created: {output_file}"
            )

        return RenderedShort(
            file_path=str(output_file),
            highlight=highlight,
            width=self.OUTPUT_WIDTH,
            height=self.OUTPUT_HEIGHT,
        )
