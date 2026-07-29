# src/services/video_analysis_proxy.py

"""Create a lightweight proxy for fast scene and motion analysis."""

from __future__ import annotations

from pathlib import Path
import subprocess


class VideoAnalysisProxy:
    """Generate a low-resolution, low-frame-rate analysis proxy."""

    def __init__(
        self,
        maximum_width: int = 960,
        frame_rate: int = 15,
    ) -> None:
        if maximum_width <= 0:
            raise ValueError("maximum_width must be positive.")

        if frame_rate <= 0:
            raise ValueError("frame_rate must be positive.")

        self.maximum_width = maximum_width
        self.frame_rate = frame_rate

    def create(
        self,
        input_video: str,
        output_video: str,
    ) -> str:
        """Create or reuse an analysis proxy."""

        input_path = Path(input_video).expanduser().resolve()
        output_path = Path(output_video).expanduser().resolve()

        if not input_path.is_file():
            raise FileNotFoundError(
                f"Input video does not exist: {input_path}"
            )

        if (
            output_path.is_file()
            and output_path.stat().st_size > 0
            and output_path.stat().st_mtime
            >= input_path.stat().st_mtime
        ):
            return str(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = output_path.with_suffix(".temporary.mp4")

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-an",
            "-vf",
            (
                f"scale='min({self.maximum_width},iw)':-2,"
                f"fps={self.frame_rate}"
            ),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(temporary_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            temporary_path.unlink(missing_ok=True)
            raise RuntimeError(
                "FFmpeg failed to create the analysis proxy:\n"
                f"{result.stderr.strip()}"
            )

        if (
            not temporary_path.is_file()
            or temporary_path.stat().st_size == 0
        ):
            raise RuntimeError(
                "Analysis proxy was not created correctly."
            )

        temporary_path.replace(output_path)
        return str(output_path)
