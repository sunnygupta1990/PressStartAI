import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.highlight_selector import HighlightSelector


def main() -> None:
    scores = [
        HighlightScore(
            features=HighlightFeatures(
                scene_start_seconds=21.00,
                scene_end_seconds=26.17,
                scene_duration_seconds=5.17,
                transcript_text="test speech",
                has_speech=True,
                speech_character_count=11,
                speech_word_count=2,
                average_motion_score=12.48,
                maximum_motion_score=48.56,
                average_audio_rms=0.203,
                maximum_audio_rms=0.372,
            ),
            speech_score=1.0,
            motion_score=0.6315,
            audio_score=1.0,
            final_score=0.8342,
        ),
        HighlightScore(
            features=HighlightFeatures(
                scene_start_seconds=28.90,
                scene_end_seconds=31.30,
                scene_duration_seconds=2.40,
                transcript_text="I was going good.",
                has_speech=True,
                speech_character_count=17,
                speech_word_count=4,
                average_motion_score=19.76,
                maximum_motion_score=32.42,
                average_audio_rms=0.127,
                maximum_audio_rms=0.225,
            ),
            speech_score=0.2353,
            motion_score=1.0,
            audio_score=0.6282,
            final_score=0.6776,
        ),
        HighlightScore(
            features=HighlightFeatures(
                scene_start_seconds=13.77,
                scene_end_seconds=21.00,
                scene_duration_seconds=7.23,
                transcript_text="",
                has_speech=False,
                speech_character_count=0,
                speech_word_count=0,
                average_motion_score=9.06,
                maximum_motion_score=20.63,
                average_audio_rms=0.140,
                maximum_audio_rms=0.247,
            ),
            speech_score=0.0,
            motion_score=0.4584,
            audio_score=0.6878,
            final_score=0.3782,
        ),
    ]

    selector = HighlightSelector()

    candidates = selector.select(
        scores=scores,
        video_duration_seconds=31.30,
    )

    print("=" * 60)
    print("Highlight Selector Verification")
    print("=" * 60)

    print(f"Candidates: {len(candidates)}")
    print()

    for candidate in candidates:
        print("-" * 60)
        print(f"Rank     : {candidate.rank}")
        print(
            f"Clip     : "
            f"{candidate.start_seconds:.2f}s "
            f"-> {candidate.end_seconds:.2f}s"
        )
        print(
            f"Duration : "
            f"{candidate.duration_seconds:.2f}s"
        )
        print(
            f"Score    : "
            f"{candidate.score.final_score:.4f}"
        )


if __name__ == "__main__":
    main()