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
from src.services.short_metadata_generator import ShortMetadataGenerator


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
        event_summary=(
            "Player shows a strong reaction during "
            "an intense dangerous combat encounter."
        ),
        commentary_category="reaction",
        visual_event=(
            "Player fights a dangerous parasite enemy."
        ),
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


def main() -> None:
    print("=" * 60)
    print("Short Metadata Generator Verification")
    print("=" * 60)

    final_highlight = create_final_highlight()

    generator = ShortMetadataGenerator()

    metadata = generator.generate(
        final_highlight
    )

    print(f"Rank             : {metadata.rank}")
    print(f"Hook             : {metadata.hook}")
    print(f"Title            : {metadata.title}")
    print(f"Description      : {metadata.description}")
    print(
        f"Hashtags         : "
        f"{' '.join(metadata.hashtags)}"
    )
    print(
        f"Thumbnail Prompt : "
        f"{metadata.thumbnail_prompt}"
    )

    if not metadata.hook:
        raise RuntimeError(
            "Generated hook is empty."
        )

    if not metadata.title:
        raise RuntimeError(
            "Generated title is empty."
        )

    if len(metadata.title) > 70:
        raise RuntimeError(
            "Generated title exceeds 70 characters."
        )

    if not metadata.description:
        raise RuntimeError(
            "Generated description is empty."
        )

    if not metadata.hashtags:
        raise RuntimeError(
            "Generated hashtags are empty."
        )

    if any(
        not hashtag.startswith("#")
        for hashtag in metadata.hashtags
    ):
        raise RuntimeError(
            "Every hashtag must begin with #."
        )

    if not metadata.thumbnail_prompt:
        raise RuntimeError(
            "Generated thumbnail prompt is empty."
        )

    print()
    print(
        "ShortMetadataGenerator verification successful."
    )


if __name__ == "__main__":
    main()