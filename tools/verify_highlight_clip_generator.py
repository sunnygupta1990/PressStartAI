import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.highlight_clip_generator import HighlightClipGenerator


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)

OUTPUT_FOLDER = "temp/highlight_clips"


def create_candidate(
    rank: int,
    start_seconds: float,
    end_seconds: float,
    final_score: float,
) -> HighlightCandidate:
    features = HighlightFeatures(
        scene_start_seconds=start_seconds,
        scene_end_seconds=end_seconds,
        scene_duration_seconds=end_seconds - start_seconds,
        transcript_text="",
        has_speech=False,
        speech_character_count=0,
        speech_word_count=0,
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

    return HighlightCandidate(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        rank=rank,
        score=score,
    )


def main() -> None:
    candidates = [
        create_candidate(
            rank=1,
            start_seconds=18.00,
            end_seconds=29.17,
            final_score=0.8342,
        ),
        create_candidate(
            rank=4,
            start_seconds=0.00,
            end_seconds=12.17,
            final_score=0.4806,
        ),
    ]

    generator = HighlightClipGenerator()

    generated_files = generator.generate(
        video_file=VIDEO_FILE,
        candidates=candidates,
        output_folder=OUTPUT_FOLDER,
    )

    print("=" * 60)
    print("Highlight Clip Generator Verification")
    print("=" * 60)

    print(f"Generated Clips: {len(generated_files)}")
    print()

    for file_path in generated_files:
        path = Path(file_path)

        print("-" * 60)
        print(f"File   : {path}")
        print(f"Exists : {path.is_file()}")

        if path.is_file():
            print(
                f"Size   : "
                f"{path.stat().st_size / 1024 / 1024:.2f} MB"
            )


if __name__ == "__main__":
    main()