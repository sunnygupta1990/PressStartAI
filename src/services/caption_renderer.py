import subprocess
from pathlib import Path


class CaptionRenderer:
    """Burn SRT captions into a rendered vertical Short."""

    def render(
        self,
        video_file: str,
        subtitle_file: str,
        output_file: str,
    ) -> str:
        video_path = Path(
            video_file
        )

        subtitle_path = Path(
            subtitle_file
        )

        output_path = Path(
            output_file
        )

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Short video does not exist: "
                f"{video_path}"
            )

        if not subtitle_path.is_file():
            raise FileNotFoundError(
                f"Subtitle file does not exist: "
                f"{subtitle_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        subtitle_filter_path = str(
            subtitle_path.resolve()
        ).replace(
            "\\",
            "/",
        )

        subtitle_filter_path = (
            subtitle_filter_path
            .replace(
                ":",
                "\\:",
            )
            .replace(
                "'",
                "\\'",
            )
        )

        video_filter = (
            "subtitles='"
            f"{subtitle_filter_path}"
            "':"
            "force_style='"
            "Alignment=2,"
            "FontSize=18,"
            "Bold=1,"
            "Outline=3,"
            "Shadow=1,"
            "MarginV=220"
            "'"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode != 0:
            raise RuntimeError(
                "FFmpeg failed to render captions: "
                f"{process.stderr}"
            )

        if not output_path.is_file():
            raise RuntimeError(
                "Captioned Short was not created: "
                f"{output_path}"
            )

        return str(
            output_path
        )