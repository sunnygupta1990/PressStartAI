import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_fusion import HighlightFusion
from src.models.highlight_score import HighlightScore
from src.services.final_highlight_combiner import FinalHighlightCombiner
from src.services.short_batch_renderer import ShortBatchRenderer


OUTPUT_FOLDER = "temp/verify_batch_shorts"


def create_generated_highlight(
    file_path: str,
    rank: int,
    start_seconds: float,
    end_seconds: float,
    transcript_text: str,
    final_score: float,
) -> GeneratedHighlight:
    features = HighlightFeatures(
        scene_start_seconds=start_seconds,
        scene_end_seconds=end_seconds,
        scene_duration_seconds=end_seconds - start_seconds,
        transcript_text=transcript_text,
        has_speech=bool(transcript_text),
        speech_character_count=len(transcript_text),
        speech_word_count=len(transcript_text.split()),
        average_motion_score=0.0,
        maximum_motion_score=0.0,
        average_audio_rms=0.0,
        maximum_audio_rms=0.0,
    )

    score = HighlightScore(
        features=features,
        speech_score=0.0,
        motion_score=0.0,
        audio_score=0.0,
        final_score=final_score,
    )

    candidate = HighlightCandidate(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        rank=rank,
        score=score,
    )

    return GeneratedHighlight(
        file_path=file_path,
        candidate=candidate,
    )


def read_video_dimensions(
    video_file: str,
) -> tuple[int, int]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        video_file,
    ]

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed: {process.stderr}"
        )

    width_text, height_text = (
        process.stdout.strip().split(
            "x",
            maxsplit=1,
        )
    )

    return int(width_text), int(height_text)


def main() -> None:
    print("=" * 60)
    print("Short Batch Renderer Verification")
    print("=" * 60)

    generated_highlights = [
        create_generated_highlight(
            file_path=(
                "temp/final_highlights/"
                "highlight_001.mp4"
            ),
            rank=1,
            start_seconds=18.0,
            end_seconds=29.17,
            transcript_text="Test reaction",
            final_score=0.8342,
        ),
        create_generated_highlight(
            file_path=(
                "temp/final_highlights/"
                "highlight_002.mp4"
            ),
            rank=4,
            start_seconds=0.0,
            end_seconds=12.17,
            transcript_text="Test rage",
            final_score=0.4806,
        ),
    ]

    approved_results = [
        HighlightFusion(
            rank=1,
            keep_highlight=True,
            category="reaction",
            event_summary="Strong reaction moment.",
            commentary_category="reaction",
            visual_event="Dangerous combat encounter.",
            action_level="high",
            danger_level="high",
            final_confidence=0.95,
            reason="Strong reaction highlight.",
        ),
        HighlightFusion(
            rank=4,
            keep_highlight=True,
            category="rage",
            event_summary="Strong rage moment.",
            commentary_category="rage",
            visual_event="Intense combat.",
            action_level="high",
            danger_level="high",
            final_confidence=0.93,
            reason="Strong rage highlight.",
        ),
    ]

    combiner = FinalHighlightCombiner()

    final_highlights = combiner.combine(
        highlights=generated_highlights,
        approved_results=approved_results,
    )

    renderer = ShortBatchRenderer()

    rendered_shorts = renderer.render(
        highlights=final_highlights,
        output_folder=OUTPUT_FOLDER,
    )

    print(
        f"Rendered Shorts : "
        f"{len(rendered_shorts)}"
    )

    if len(rendered_shorts) != 2:
        raise RuntimeError(
            "Expected exactly two rendered Shorts."
        )

    for rendered_short in rendered_shorts:
        width, height = read_video_dimensions(
            rendered_short.file_path
        )

        print()
        print("-" * 60)
        print(
            f"Rank       : "
            f"{rendered_short.rank}"
        )
        print(
            f"File       : "
            f"{rendered_short.file_path}"
        )
        print(
            f"Dimensions : "
            f"{width}x{height}"
        )
        print(
            f"Category   : "
            f"{rendered_short.category}"
        )

        if width != 1080 or height != 1920:
            raise RuntimeError(
                "Rendered Short has invalid dimensions."
            )

    print()
    print(
        "ShortBatchRenderer verification successful."
    )


if __name__ == "__main__":
    main()