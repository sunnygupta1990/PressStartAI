import json
import shutil
from pathlib import Path

from src.models.final_highlight import FinalHighlight


class FinalHighlightExporter:
    """Export final approved highlights and metadata."""

    def export(
        self,
        highlights: list[FinalHighlight],
        output_folder: str,
    ) -> list[str]:
        output_path = Path(output_folder)

        clips_path = output_path / "clips"
        metadata_path = output_path / "metadata"

        clips_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        metadata_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._clear_output_folder(
            clips_path=clips_path,
            metadata_path=metadata_path,
        )

        exported_files: list[str] = []

        for index, highlight in enumerate(
            highlights,
            start=1,
        ):
            source_file = Path(
                highlight.file_path
            )

            if not source_file.is_file():
                raise FileNotFoundError(
                    f"Highlight clip does not exist: "
                    f"{source_file}"
                )

            clip_filename = (
                f"highlight_{index:03d}.mp4"
            )

            metadata_filename = (
                f"highlight_{index:03d}.json"
            )

            output_clip = (
                clips_path / clip_filename
            )

            output_metadata = (
                metadata_path / metadata_filename
            )

            shutil.copy2(
                source_file,
                output_clip,
            )

            metadata = {
                "rank": highlight.rank,
                "source_start_seconds": (
                    highlight.start_seconds
                ),
                "source_end_seconds": (
                    highlight.end_seconds
                ),
                "duration_seconds": (
                    highlight.duration_seconds
                ),
                "heuristic_score": (
                    highlight.heuristic_score
                ),
                "category": highlight.category,
                "event_summary": (
                    highlight.event_summary
                ),
                "commentary_category": (
                    highlight.commentary_category
                ),
                "visual_event": (
                    highlight.visual_event
                ),
                "action_level": (
                    highlight.action_level
                ),
                "danger_level": (
                    highlight.danger_level
                ),
                "confidence": (
                    highlight.confidence
                ),
                "transcript": (
                    highlight.transcript_text
                ),
                "reason": highlight.reason,
                "clip_file": clip_filename,
            }

            output_metadata.write_text(
                json.dumps(
                    metadata,
                    ensure_ascii=False,
                    indent=4,
                ),
                encoding="utf-8",
            )

            exported_files.append(
                str(output_clip)
            )

        return exported_files

    @staticmethod
    def _clear_output_folder(
        clips_path: Path,
        metadata_path: Path,
    ) -> None:
        for old_file in clips_path.glob(
            "highlight_*.mp4"
        ):
            old_file.unlink()

        for old_file in metadata_path.glob(
            "highlight_*.json"
        ):
            old_file.unlink()