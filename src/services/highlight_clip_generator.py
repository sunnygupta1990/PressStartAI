# src/services/highlight_clip_generator.py

"""Generate lightweight analysis clips and source-quality highlight clips."""

from __future__ import annotations

from pathlib import Path
import subprocess

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate


class HighlightClipGenerator:
    """Generate clips from selected highlight candidates."""

    def generate(
        self,
        video_file: str,
        candidates: list[HighlightCandidate],
        output_folder: str,
        *,
        analysis_mode: bool = False,
    ) -> list[GeneratedHighlight]:
        """Generate clips for AI analysis or final rendering."""

        video_path = Path(video_file).expanduser().resolve()

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file does not exist: {video_path}"
            )

        output_path = Path(output_folder).expanduser().resolve()
        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        for old_file in output_path.glob("highlight_*.mp4"):
            old_file.unlink()

        generated_highlights: list[GeneratedHighlight] = []

        for index, candidate in enumerate(candidates, start=1):
            output_file = output_path / f"highlight_{index:03d}.mp4"

            if analysis_mode:
                self._generate_analysis_clip(
                    video_path=video_path,
                    candidate=candidate,
                    output_file=output_file,
                )
            else:
                self._generate_source_clip(
                    video_path=video_path,
                    candidate=candidate,
                    output_file=output_file,
                )

            generated_highlights.append(
                GeneratedHighlight(
                    file_path=str(output_file),
                    candidate=candidate,
                )
            )

        return generated_highlights

    @staticmethod
    def _generate_analysis_clip(
        video_path: Path,
        candidate: HighlightCandidate,
        output_file: Path,
    ) -> None:
        """Create a small clip suitable for local AI analysis."""

        duration = candidate.end_seconds - candidate.start_seconds

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{candidate.start_seconds:.3f}",
            "-i",
            str(video_path),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            "scale='min(960,iw)':-2,fps=15",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-movflags",
            "+faststart",
            str(output_file),
        ]

        HighlightClipGenerator._run(command, output_file)

    @staticmethod
    def _generate_source_clip(
        video_path: Path,
        candidate: HighlightCandidate,
        output_file: Path,
    ) -> None:
        """Extract the approved source interval without re-encoding."""

        duration = candidate.end_seconds - candidate.start_seconds

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{candidate.start_seconds:.3f}",
            "-i",
            str(video_path),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-movflags",
            "+faststart",
            str(output_file),
        ]

        HighlightClipGenerator._run(command, output_file)

    @staticmethod
    def _run(
        command: list[str],
        output_file: Path,
    ) -> None:
        """Run FFmpeg and validate its output."""

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FFmpeg failed to generate a highlight clip:\n"
                f"{result.stderr.strip()}"
            )

        if not output_file.is_file() or output_file.stat().st_size == 0:
            raise RuntimeError(
                f"Highlight clip was not created: {output_file}"
            )
