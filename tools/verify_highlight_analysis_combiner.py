import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_reasoning import HighlightReasoning
from src.models.highlight_score import HighlightScore
from src.services.highlight_analysis_combiner import HighlightAnalysisCombiner


def create_highlight(
    rank: int,
    start_seconds: float,
    end_seconds: float,
    final_score: float,
    transcript_text: str,
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
        file_path=f"temp/highlight_{rank:03d}.mp4",
        candidate=candidate,
    )


def main() -> None:
    highlights = [
        create_highlight(
            rank=1,
            start_seconds=18.00,
            end_seconds=29.17,
            final_score=0.8342,
            transcript_text="Test reaction",
        ),
        create_highlight(
            rank=4,
            start_seconds=0.00,
            end_seconds=12.17,
            final_score=0.4806,
            transcript_text="Test rage",
        ),
    ]

    reasoning_results = [
        HighlightReasoning(
            rank=1,
            is_interesting=True,
            category="reaction",
            reason="Strong reaction moment.",
            confidence=0.75,
        ),
        HighlightReasoning(
            rank=4,
            is_interesting=True,
            category="rage",
            reason="Frustrated gameplay reaction.",
            confidence=0.90,
        ),
    ]

    combiner = HighlightAnalysisCombiner()

    analyzed_highlights = combiner.combine(
        highlights=highlights,
        reasoning_results=reasoning_results,
    )

    print("=" * 60)
    print("Highlight Analysis Combiner Verification")
    print("=" * 60)

    print(
        f"Analyzed Highlights: "
        f"{len(analyzed_highlights)}"
    )
    print()

    for highlight in analyzed_highlights:
        print("-" * 60)
        print(f"Rank        : {highlight.rank}")
        print(f"File        : {highlight.file_path}")
        print(
            f"Timeline    : "
            f"{highlight.start_seconds:.2f}s "
            f"-> {highlight.end_seconds:.2f}s"
        )
        print(
            f"Duration    : "
            f"{highlight.duration_seconds:.2f}s"
        )
        print(
            f"Final Score : "
            f"{highlight.final_score:.4f}"
        )
        print(
            f"Interesting : "
            f"{highlight.is_interesting}"
        )
        print(f"Category    : {highlight.category}")
        print(
            f"Confidence  : "
            f"{highlight.confidence:.4f}"
        )
        print(f"Reason      : {highlight.reason}")


if __name__ == "__main__":
    main()