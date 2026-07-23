# src/services/ranking_video_service.py

"""Create vertical ranking videos from manually ranked source clips."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Sequence


class RankingVideoError(RuntimeError):
    """Raised when a ranking video cannot be created."""


@dataclass(frozen=True, slots=True)
class RankingClip:
    """One manually ranked source video."""

    video_path: Path
    rank: int
    description: str

    def normalized(self) -> "RankingClip":
        """Return a normalized copy of the ranking clip."""

        return RankingClip(
            video_path=self.video_path.expanduser().resolve(),
            rank=self.rank,
            description=self.description.strip(),
        )


@dataclass(frozen=True, slots=True)
class RankingVideoSettings:
    """Rendering settings for one ranking video."""

    output_width: int = 1080
    output_height: int = 1920
    clip_duration_seconds: float = 5.0
    frame_rate: int = 30
    video_crf: int = 20
    video_preset: str = "medium"
    rank_font_size: int = 190
    description_font_size: int = 82
    background_color: str = "black"


class RankingVideoService:
    """Render multiple manually ranked clips into one vertical video."""

    def __init__(
        self,
        settings: RankingVideoSettings | None = None,
        ffmpeg_path: str | None = None,
        ffprobe_path: str | None = None,
    ) -> None:
        self.settings = settings or RankingVideoSettings()
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg")
        self.ffprobe_path = ffprobe_path or shutil.which("ffprobe")

        self._validate_settings()
        self._validate_tools()

    def render(
        self,
        clips: Sequence[RankingClip],
        output_path: str | Path,
    ) -> Path:
        """Render one vertical ranking video."""

        normalized_clips = [
            clip.normalized()
            for clip in clips
        ]
        normalized_output = Path(output_path).expanduser().resolve()

        self._validate_clips(normalized_clips)
        self._validate_output_path(normalized_output)

        ordered_clips = sorted(
            normalized_clips,
            key=lambda clip: clip.rank,
            reverse=True,
        )

        normalized_output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.TemporaryDirectory(
            prefix="pressstartai_ranking_"
        ) as temporary_directory:
            temporary_path = Path(temporary_directory)

            rendered_clips = self._render_clips(
                clips=ordered_clips,
                temporary_directory=temporary_path,
            )

            concat_file = self._create_concat_file(
                rendered_clips=rendered_clips,
                temporary_directory=temporary_path,
            )

            temporary_output = (
                temporary_path / "ranking_video_final.mp4"
            )

            self._concatenate_clips(
                concat_file=concat_file,
                output_path=temporary_output,
            )

            if (
                not temporary_output.exists()
                or temporary_output.stat().st_size == 0
            ):
                raise RankingVideoError(
                    "FFmpeg completed without creating a valid ranking video."
                )

            shutil.copy2(
                temporary_output,
                normalized_output,
            )

        return normalized_output

    def _render_clips(
        self,
        clips: Sequence[RankingClip],
        temporary_directory: Path,
    ) -> list[Path]:
        """Render all normalized ranking clips."""

        rendered_clips: list[Path] = []

        for index, clip in enumerate(clips, start=1):
            rendered_path = (
                temporary_directory
                / f"ranking_clip_{index:03d}.mp4"
            )

            print(
                f"Rendering rank #{clip.rank}: "
                f"{clip.description}"
            )

            self._render_clip(
                clip=clip,
                output_path=rendered_path,
            )

            rendered_clips.append(rendered_path)

        return rendered_clips

    def _render_clip(
        self,
        clip: RankingClip,
        output_path: Path,
    ) -> None:
        """Render one ranked vertical clip."""

        settings = self.settings
        escaped_description = self._escape_drawtext(
            clip.description.upper()
        )

        video_filter = (
            f"scale={settings.output_width}:{settings.output_height}:"
            "force_original_aspect_ratio=increase,"
            f"crop={settings.output_width}:{settings.output_height},"
            f"fps={settings.frame_rate},"
            "setsar=1,"
            "drawbox="
            "x=0:"
            "y=0:"
            f"w={settings.output_width}:"
            "h=330:"
            "color=black@0.55:"
            "t=fill,"
            "drawtext="
            f"text='#{clip.rank}':"
            "fontcolor=white:"
            f"fontsize={settings.rank_font_size}:"
            "borderw=8:"
            "bordercolor=black@0.85:"
            "x=(w-text_w)/2:"
            "y=38,"
            "drawtext="
            f"text='{escaped_description}':"
            "fontcolor=white:"
            f"fontsize={settings.description_font_size}:"
            "borderw=5:"
            "bordercolor=black@0.85:"
            "x=(w-text_w)/2:"
            "y=235"
        )

        command = [
            str(self.ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(clip.video_path),
            "-t",
            f"{settings.clip_duration_seconds:.3f}",
            "-vf",
            video_filter,
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            settings.video_preset,
            "-crf",
            str(settings.video_crf),
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(settings.frame_rate),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output_path),
        ]

        self._run_command(
            command=command,
            failure_message=(
                f"Unable to render rank #{clip.rank} "
                f"from {clip.video_path.name}."
            ),
        )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RankingVideoError(
                f"Rendered clip was not created for rank #{clip.rank}."
            )

    def _create_concat_file(
        self,
        rendered_clips: Sequence[Path],
        temporary_directory: Path,
    ) -> Path:
        """Create an FFmpeg concat manifest."""

        concat_path = temporary_directory / "ranking_concat.txt"

        lines = [
            f"file '{self._escape_concat_path(path)}'"
            for path in rendered_clips
        ]

        concat_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        return concat_path

    def _concatenate_clips(
        self,
        concat_file: Path,
        output_path: Path,
    ) -> None:
        """Concatenate all rendered clips into the final MP4."""

        command = [
            str(self.ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        self._run_command(
            command=command,
            failure_message="Unable to concatenate ranking clips.",
        )

    def _validate_clips(
        self,
        clips: Sequence[RankingClip],
    ) -> None:
        """Validate all ranking-video inputs."""

        if len(clips) < 2:
            raise RankingVideoError(
                "At least two clips are required to create a ranking video."
            )

        ranks: set[int] = set()

        for clip in clips:
            if not clip.video_path.exists():
                raise RankingVideoError(
                    f"Video file was not found: {clip.video_path}"
                )

            if not clip.video_path.is_file():
                raise RankingVideoError(
                    f"Video path is not a file: {clip.video_path}"
                )

            if clip.video_path.suffix.lower() != ".mp4":
                raise RankingVideoError(
                    f"Only MP4 files are supported: {clip.video_path.name}"
                )

            if clip.rank <= 0:
                raise RankingVideoError(
                    f"Rank must be greater than zero: {clip.rank}"
                )

            if clip.rank in ranks:
                raise RankingVideoError(
                    f"Duplicate rank detected: #{clip.rank}"
                )

            ranks.add(clip.rank)

            if not clip.description:
                raise RankingVideoError(
                    f"Rank #{clip.rank} requires a description."
                )

            if not self._is_one_word(clip.description):
                raise RankingVideoError(
                    f"Description for rank #{clip.rank} must be one word."
                )

            if len(clip.description) > 24:
                raise RankingVideoError(
                    f"Description for rank #{clip.rank} "
                    "cannot exceed 24 characters."
                )

            self._validate_video_stream(clip.video_path)

    def _validate_video_stream(
        self,
        video_path: Path,
    ) -> None:
        """Verify that a file contains a readable video stream."""

        command = [
            str(self.ffprobe_path),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_message = (
                result.stderr.strip()
                or "FFprobe could not read the file."
            )
            raise RankingVideoError(
                f"Invalid video {video_path.name}: {error_message}"
            )

        if "video" not in result.stdout.lower():
            raise RankingVideoError(
                f"No video stream was found in {video_path.name}."
            )

    def _validate_output_path(
        self,
        output_path: Path,
    ) -> None:
        """Validate the requested output path."""

        if output_path.suffix.lower() != ".mp4":
            raise RankingVideoError(
                "Ranking-video output must use the .mp4 extension."
            )

        if output_path.exists() and output_path.is_dir():
            raise RankingVideoError(
                f"Output path is a directory: {output_path}"
            )

    def _validate_settings(self) -> None:
        """Validate rendering settings."""

        settings = self.settings

        if settings.output_width <= 0 or settings.output_height <= 0:
            raise RankingVideoError(
                "Output dimensions must be greater than zero."
            )

        if settings.output_width % 2 or settings.output_height % 2:
            raise RankingVideoError(
                "Output dimensions must be even numbers."
            )

        if settings.clip_duration_seconds <= 0:
            raise RankingVideoError(
                "Clip duration must be greater than zero."
            )

        if settings.frame_rate <= 0:
            raise RankingVideoError(
                "Frame rate must be greater than zero."
            )

        if not 0 <= settings.video_crf <= 51:
            raise RankingVideoError(
                "Video CRF must be between 0 and 51."
            )

    def _validate_tools(self) -> None:
        """Ensure FFmpeg and FFprobe are available."""

        if not self.ffmpeg_path:
            raise RankingVideoError(
                "FFmpeg was not found on PATH."
            )

        if not self.ffprobe_path:
            raise RankingVideoError(
                "FFprobe was not found on PATH."
            )

    def _run_command(
        self,
        command: Sequence[str],
        failure_message: str,
    ) -> None:
        """Run one FFmpeg command with readable failure output."""

        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return

        error_message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown FFmpeg error."
        )

        raise RankingVideoError(
            f"{failure_message}\n{error_message}"
        )

    @staticmethod
    def _is_one_word(value: str) -> bool:
        """Return whether a label contains exactly one visible word."""

        return bool(
            re.fullmatch(
                r"[^\s]+",
                value.strip(),
            )
        )

    @staticmethod
    def _escape_drawtext(value: str) -> str:
        """Escape text for FFmpeg's drawtext filter."""

        escaped = value.replace("\\", r"\\")
        escaped = escaped.replace(":", r"\:")
        escaped = escaped.replace("'", r"\'")
        escaped = escaped.replace("%", r"\%")
        escaped = escaped.replace(",", r"\,")

        return escaped

    @staticmethod
    def _escape_concat_path(path: Path) -> str:
        """Escape a path for an FFmpeg concat manifest."""

        normalized = path.resolve().as_posix()
        return normalized.replace("'", r"'\''")