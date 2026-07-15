import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.highlight_overlap_resolver import HighlightOverlapResolver


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
            rank=2,
            start_seconds=25.90,
            end_seconds=31.30,
            final_score=0.6776,
        ),
        create_candidate(
            rank=3,
            start_seconds=23.17,
            end_seconds=31.30,
            final_score=0.5507,
        ),
        create_candidate(
            rank=4,
            start_seconds=0.00,
            end_seconds=12.17,
            final_score=0.4806,
        ),
    ]

    resolver = HighlightOverlapResolver()

    resolved = resolver.resolve(candidates)

    print("=" * 60)
    print("Highlight Overlap Resolver Verification")
    print("=" * 60)

    print(f"Input Candidates   : {len(candidates)}")
    print(f"Resolved Candidates: {len(resolved)}")
    print()

    for candidate in resolved:
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