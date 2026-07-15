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


def create_generated_highlight(
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
        file_path=f"temp/final_highlights/highlight_{rank:03d}.mp4",
        candidate=candidate,
    )


def main() -> None:
    highlights = [
        create_generated_highlight(
            rank=1,
            start_seconds=18.00,
            end_seconds=29.17,
            final_score=0.8342,
            transcript_text="Test reaction",
        ),
        create_generated_highlight(
            rank=4,
            start_seconds=0.00,
            end_seconds=12.17,
            final_score=0.4806,
            transcript_text="Test rage",
        ),
    ]

    approved_results = [
        HighlightFusion(
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
        ),
        HighlightFusion(
            rank=4,
            keep_highlight=True,
            category="rage",
            event_summary="Strong frustrated combat moment.",
            commentary_category="rage",
            visual_event="Player fighting multiple enemies.",
            action_level="high",
            danger_level="high",
            final_confidence=0.93,
            reason="Strong multimodal rage highlight.",
        ),
    ]

    combiner = FinalHighlightCombiner()

    final_highlights = combiner.combine(
        highlights=highlights,
        approved_results=approved_results,
    )

    print("=" * 60)
    print("Final Highlight Combiner Verification")
    print("=" * 60)

    print(f"Final Highlights: {len(final_highlights)}")
    print()

    for highlight in final_highlights:
        print("-" * 60)
        print(f"Rank            : {highlight.rank}")
        print(f"File            : {highlight.file_path}")
        print(
            f"Timeline        : "
            f"{highlight.start_seconds:.2f}s "
            f"-> {highlight.end_seconds:.2f}s"
        )
        print(
            f"Duration        : "
            f"{highlight.duration_seconds:.2f}s"
        )
        print(
            f"Heuristic Score : "
            f"{highlight.heuristic_score:.4f}"
        )
        print(f"Category        : {highlight.category}")
        print(
            f"Confidence      : "
            f"{highlight.confidence:.4f}"
        )
        print(
            f"Event Summary   : "
            f"{highlight.event_summary}"
        )


if __name__ == "__main__":
    main()