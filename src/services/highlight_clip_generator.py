from pathlib import Path

import ffmpeg

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate


class HighlightClipGenerator:
    """Generate video clips from selected highlight candidates."""

    def generate(
        self,
        video_file: str,
        candidates: list[HighlightCandidate],
        output_folder: str,
    ) -> list[GeneratedHighlight]:
        video_path = Path(video_file)

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file does not exist: {video_path}"
            )

        output_path = Path(output_folder)
        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        for old_file in output_path.glob(
            "highlight_*.mp4"
        ):
            old_file.unlink()

        generated_highlights: list[GeneratedHighlight] = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            output_file = output_path / (
                f"highlight_{index:03d}.mp4"
            )

            duration_seconds = (
                candidate.end_seconds
                - candidate.start_seconds
            )

            input_stream = ffmpeg.input(
                str(video_path),
                ss=candidate.start_seconds,
                t=duration_seconds,
            )

            video_stream = input_stream.video
            audio_stream = input_stream.audio

            output_stream = ffmpeg.output(
                video_stream,
                audio_stream,
                str(output_file),
                vcodec="libx264",
                acodec="aac",
                preset="fast",
                movflags="+faststart",
            )

            ffmpeg.run(
                output_stream,
                overwrite_output=True,
                quiet=True,
            )

            generated_highlights.append(
                GeneratedHighlight(
                    file_path=str(output_file),
                    candidate=candidate,
                )
            )

        return generated_highlights