import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_fusion import HighlightFusion
from src.models.highlight_score import HighlightScore
from src.services.caption_segment_builder import CaptionSegmentBuilder
from src.services.final_highlight_combiner import FinalHighlightCombiner


def create_final_highlight():
    transcript_text = (
        "बाग बाग बाग बाग गलत हक्किया "
        "चलो उस पेल ने बचा लिया मेरे को"
    )

    features = HighlightFeatures(
        scene_start_seconds=21.0,
        scene_end_seconds=26.17,
        scene_duration_seconds=5.17,
        transcript_text=transcript_text,
        has_speech=True,
        speech_character_count=len(transcript_text),
        speech_word_count=len(transcript_text.split()),
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
        file_path=(
            "temp/final_highlights/"
            "highlight_001.mp4"
        ),
        candidate=candidate,
    )

    fusion = HighlightFusion(
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


def main() -> None:
    print("=" * 60)
    print("Caption Segment Builder Verification")
    print("=" * 60)

    final_highlight = create_final_highlight()

    builder = CaptionSegmentBuilder(
        maximum_words_per_caption=4,
    )

    captions = builder.build(
        final_highlight
    )

    print(
        f"Caption Segments : "
        f"{len(captions)}"
    )

    if not captions:
        raise RuntimeError(
            "No caption segments were created."
        )

    for index, caption in enumerate(
        captions,
        start=1,
    ):
        print()
        print("-" * 60)
        print(f"Caption {index}")
        print(
            f"Timeline : "
            f"{caption.start_seconds:.2f}s "
            f"-> {caption.end_seconds:.2f}s"
        )
        print(f"Text     : {caption.text}")

        if len(caption.text.split()) > 4:
            raise RuntimeError(
                "Caption exceeds the maximum word count."
            )

    if captions[0].start_seconds != 0.0:
        raise RuntimeError(
            "First caption must start at zero."
        )

    if (
        abs(
            captions[-1].end_seconds
            - final_highlight.duration_seconds
        )
        > 0.001
    ):
        raise RuntimeError(
            "Last caption must end at highlight duration."
        )

    print()
    print(
        "CaptionSegmentBuilder verification successful."
    )


if __name__ == "__main__":
    main()