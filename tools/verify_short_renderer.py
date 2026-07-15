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
from src.services.short_renderer import ShortRenderer


HIGHLIGHT_FILE = (
    "temp/final_highlights/highlight_001.mp4"
)

OUTPUT_FOLDER = "temp/verify_shorts"


def create_final_highlight():
    features = HighlightFeatures(
        scene_start_seconds=21.0,
        scene_end_seconds=26.17,
        scene_duration_seconds=5.17,
        transcript_text="Test reaction",
        has_speech=True,
        speech_character_count=13,
        speech_word_count=2,
        average_motion_score=12.0,
        maximum_motion_score=48.0,
        average_audio_rms=0.20,
        maximum_audio_rms=0.37,
    )

    score = HighlightScore(
        features=features,
        speech_score=1.0,
        motion_score=0.63,
        audio_score=1.0,
        final_score=0.8342,
    )

    candidate = HighlightCandidate(
        start_seconds=18.0,
        end_seconds=29.17,
        rank=1,
        score=score,
    )

    generated_highlight = GeneratedHighlight(
        file_path=HIGHLIGHT_FILE,
        candidate=candidate,
    )

    fusion = HighlightFusion(
        rank=1,
        keep_highlight=True,
        category="reaction",
        event_summary="Strong boss-fight reaction.",
        commentary_category="reaction",
        visual_event="Player fighting a dangerous enemy.",
        action_level="high",
        danger_level="high",
        final_confidence=0.95,
        reason="Strong multimodal reaction highlight.",
    )

    combiner = FinalHighlightCombiner()

    final_highlights = combiner.combine(
        highlights=[generated_highlight],
        approved_results=[fusion],
    )

    if not final_highlights:
        raise RuntimeError(
            "Final highlight was not created."
        )

    return final_highlights[0]


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

    dimensions = process.stdout.strip()

    width_text, height_text = dimensions.split(
        "x",
        maxsplit=1,
    )

    return (
        int(width_text),
        int(height_text),
    )


def main() -> None:
    print("=" * 60)
    print("Short Renderer Verification")
    print("=" * 60)

    final_highlight = create_final_highlight()

    renderer = ShortRenderer()

    rendered_short = renderer.render(
        highlight=final_highlight,
        output_folder=OUTPUT_FOLDER,
    )

    width, height = read_video_dimensions(
        rendered_short.file_path
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
        f"Rank       : "
        f"{rendered_short.rank}"
    )

    print(
        f"Category   : "
        f"{rendered_short.category}"
    )

    print(
        f"Confidence : "
        f"{rendered_short.confidence:.4f}"
    )

    if width != 1080:
        raise RuntimeError(
            "Rendered Short width is not 1080."
        )

    if height != 1920:
        raise RuntimeError(
            "Rendered Short height is not 1920."
        )

    print()
    print(
        "ShortRenderer verification successful."
    )


if __name__ == "__main__":
    main()