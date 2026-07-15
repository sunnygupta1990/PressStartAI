import sys
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.visual_highlight_reasoner import VisualHighlightReasoner


FRAME_FILES = [
    "temp/verify_resized_frames/highlight_001_frame_001.jpg",
    "temp/verify_resized_frames/highlight_001_frame_002.jpg",
    "temp/verify_resized_frames/highlight_001_frame_003.jpg",
]


def create_highlight() -> GeneratedHighlight:
    features = HighlightFeatures(
        scene_start_seconds=21.0,
        scene_end_seconds=26.17,
        scene_duration_seconds=5.17,
        transcript_text="Verification transcript",
        has_speech=True,
        speech_character_count=23,
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
        final_score=0.83,
    )

    candidate = HighlightCandidate(
        start_seconds=18.0,
        end_seconds=29.17,
        rank=1,
        score=score,
    )

    return GeneratedHighlight(
        file_path="temp/final_highlights/highlight_001.mp4",
        candidate=candidate,
    )


def run_benchmark(
    reasoner: VisualHighlightReasoner,
    highlight: GeneratedHighlight,
    run_number: int,
) -> None:
    start_time = perf_counter()

    result = reasoner.reason(
        highlight=highlight,
        frame_files=FRAME_FILES,
    )

    duration = perf_counter() - start_time

    print()
    print("-" * 60)
    print(f"Run              : {run_number}")
    print(f"Duration         : {duration:.2f}s")
    print(f"Visual Event     : {result.visual_event}")
    print(f"Action Level     : {result.action_level}")
    print(f"Danger Level     : {result.danger_level}")
    print(f"Interesting      : {result.looks_interesting}")
    print(f"Confidence       : {result.confidence:.4f}")


def main() -> None:
    print("=" * 60)
    print("Visual Highlight Reasoner Benchmark")
    print("=" * 60)

    for frame_file in FRAME_FILES:
        if not Path(frame_file).is_file():
            raise FileNotFoundError(
                f"Benchmark frame does not exist: {frame_file}"
            )

    highlight = create_highlight()
    reasoner = VisualHighlightReasoner()

    run_benchmark(
        reasoner=reasoner,
        highlight=highlight,
        run_number=1,
    )

    run_benchmark(
        reasoner=reasoner,
        highlight=highlight,
        run_number=2,
    )


if __name__ == "__main__":
    main()