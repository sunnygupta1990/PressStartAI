# src/services/facecam_short_renderer.py

from pathlib import Path
import subprocess

from src.models.final_highlight import FinalHighlight
from src.models.recording_session import RecordingSession
from src.models.rendered_short import RenderedShort


class FaceCamShortRenderer:
    """Render a synchronized vertical facecam and gameplay Short."""

    OUTPUT_WIDTH = 1080
    OUTPUT_HEIGHT = 1920
    FACECAM_HEIGHT = 768
    GAMEPLAY_HEIGHT = 1152

    def validate(
        self,
        recording_session: RecordingSession,
    ) -> None:
        """Validate recordings and synchronization state."""

        if not recording_session.has_facecam_layout:
            raise ValueError(
                "Facecam Mode requires normal, gameplay, "
                "and facecam recordings."
            )

        if not recording_session.is_synchronized:
            raise ValueError(
                "Facecam recordings must be synchronized before rendering."
            )

        recordings = {
            "Normal combined": recording_session.recording_video,
            "Gameplay": recording_session.gameplay_video,
            "Facecam": recording_session.facecam_video,
        }

        for recording_name, file_name in recordings.items():
            recording_path = Path(file_name or "")

            if not recording_path.is_file():
                raise FileNotFoundError(
                    f"{recording_name} recording does not exist: "
                    f"{recording_path}"
                )

    def render(
        self,
        highlight: FinalHighlight,
        recording_session: RecordingSession,
        output_folder: str,
        subtitle_file: str | None = None,
        output_file_name: str | None = None,
    ) -> RenderedShort:
        """Render one synchronized facecam Short."""

        self.validate(recording_session)

        gameplay_start = recording_session.gameplay_timestamp(
            highlight.start_seconds
        )
        facecam_start = recording_session.facecam_timestamp(
            highlight.start_seconds
        )
        master_start = highlight.start_seconds

        self._validate_start_timestamp(
            timestamp=gameplay_start,
            recording_name="Gameplay",
        )
        self._validate_start_timestamp(
            timestamp=facecam_start,
            recording_name="Facecam",
        )
        self._validate_start_timestamp(
            timestamp=master_start,
            recording_name="Normal combined",
        )

        gameplay_path = Path(
            recording_session.gameplay_video or ""
        )
        facecam_path = Path(
            recording_session.facecam_video or ""
        )
        master_path = Path(recording_session.recording_video)

        output_path = Path(output_folder)
        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = output_path / (
            output_file_name
            or f"facecam_short_{highlight.rank:03d}.mp4"
        )

        subtitle_filter = self._build_subtitle_filter(
            subtitle_file
        )

        filter_complex = (
            f"[0:v]"
            f"scale={self.OUTPUT_WIDTH}:{self.GAMEPLAY_HEIGHT}:"
            f"force_original_aspect_ratio=increase,"
            f"crop={self.OUTPUT_WIDTH}:{self.GAMEPLAY_HEIGHT},"
            f"gblur=sigma=20,"
            f"setsar=1"
            f"[gameplay_bg];"
            f"[0:v]"
            f"scale={self.OUTPUT_WIDTH}:{self.GAMEPLAY_HEIGHT}:"
            f"force_original_aspect_ratio=decrease,"
            f"setsar=1"
            f"[gameplay_fg];"
            f"[gameplay_bg][gameplay_fg]"
            f"overlay=(W-w)/2:(H-h)/2,"
            f"setsar=1"
            f"[gameplay];"
            f"[1:v]"
            f"scale={self.OUTPUT_WIDTH}:{self.FACECAM_HEIGHT}:"
            f"force_original_aspect_ratio=increase,"
            f"crop={self.OUTPUT_WIDTH}:{self.FACECAM_HEIGHT},"
            f"setsar=1"
            f"[facecam];"
            f"[facecam][gameplay]"
            f"vstack=inputs=2"
            f"{subtitle_filter}"
            f"[video]"
        )

        command = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{gameplay_start:.3f}",
            "-i",
            str(gameplay_path),
            "-ss",
            f"{facecam_start:.3f}",
            "-i",
            str(facecam_path),
            "-ss",
            f"{master_start:.3f}",
            "-i",
            str(master_path),
            "-t",
            f"{highlight.duration_seconds:.3f}",
            "-filter_complex",
            filter_complex,
            "-map",
            "[video]",
            "-map",
            "2:a?",
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
                "FFmpeg failed to render the Facecam Short:\n"
                f"{process.stderr}"
            )

        if not output_file.is_file():
            raise RuntimeError(
                "Facecam Short was not created: "
                f"{output_file}"
            )

        return RenderedShort(
            file_path=str(output_file),
            highlight=highlight,
            width=self.OUTPUT_WIDTH,
            height=self.OUTPUT_HEIGHT,
        )

    @staticmethod
    def _build_subtitle_filter(
        subtitle_file: str | None,
    ) -> str:
        """Build an optional subtitle filter for the final encode."""

        if not subtitle_file:
            return ""

        subtitle_path = Path(subtitle_file)

        if not subtitle_path.is_file():
            raise FileNotFoundError(
                f"Subtitle file does not exist: {subtitle_path}"
            )

        escaped_path = str(
            subtitle_path.resolve()
        ).replace(
            "\\",
            "/",
        ).replace(
            ":",
            "\\:",
        ).replace(
            "'",
            "\\'",
        )

        return (
            ",subtitles='"
            f"{escaped_path}"
            "':force_style='"
            "Alignment=2,"
            "FontSize=18,"
            "Bold=1,"
            "Outline=3,"
            "Shadow=1,"
            "MarginV=220"
            "'"
        )

    @staticmethod
    def _validate_start_timestamp(
        timestamp: float,
        recording_name: str,
    ) -> None:
        """Reject timestamps before a recording begins."""

        if timestamp < 0:
            raise RuntimeError(
                f"{recording_name} recording does not contain the "
                "beginning of this highlight after synchronization. "
                f"Calculated timestamp: {timestamp:.3f} seconds."
            )