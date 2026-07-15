import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.analyzed_highlight import AnalyzedHighlight
from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_reasoning import HighlightReasoning
from src.models.highlight_score import HighlightScore
from src.models.visual_reasoning import VisualReasoning
from src.services.highlight_fusion_reasoner import HighlightFusionReasoner


def create_analyzed_highlight() -> AnalyzedHighlight:
    transcript_text = (
        "बाग बाग बाग बाग गलत हक्किया चलो "
        "उस पेल ने बचा लिया मेरे को कभी नहीं हाँ"
    )

    features = HighlightFeatures(
        scene_start_seconds=21.00,
        scene_end_seconds=26.17,
        scene_duration_seconds=5.17,
        transcript_text=transcript_text,
        has_speech=True,
        speech_character_count=len(transcript_text),
        speech_word_count=len(transcript_text.split()),
        average_motion_score=12.4827,
        maximum_motion_score=48.5669,
        average_audio_rms=0.203682,
        maximum_audio_rms=0.372899,
    )

    score = HighlightScore(
        features=features,
        speech_score=1.0,
        motion_score=0.6315,
        audio_score=1.0,
        final_score=0.8342,
    )

    candidate = HighlightCandidate(
        start_seconds=18.00,
        end_seconds=29.17,
        rank=1,
        score=score,
    )

    generated_highlight = GeneratedHighlight(
        file_path=(
            r"temp\final_highlights\highlight_001.mp4"
        ),
        candidate=candidate,
    )

    reasoning = HighlightReasoning(
        rank=1,
        is_interesting=True,
        category="reaction",
        reason=(
            "Strong surprised or frustrated gameplay reaction."
        ),
        confidence=0.85,
    )

    return AnalyzedHighlight(
        highlight=generated_highlight,
        reasoning=reasoning,
    )


def main() -> None:
    analyzed_highlight = create_analyzed_highlight()

    visual_reasoning = VisualReasoning(
        rank=1,
        visual_event=(
            "The player is engaging in combat with "
            "a large, red enemy."
        ),
        action_level="high",
        danger_level="high",
        looks_interesting=True,
        reason=(
            "The intensity of the fight and visual "
            "effects indicate a dramatic moment."
        ),
        confidence=0.95,
    )

    reasoner = HighlightFusionReasoner()

    result = reasoner.reason(
        analyzed_highlight=analyzed_highlight,
        visual_reasoning=visual_reasoning,
    )

    print("=" * 60)
    print("Highlight Fusion Reasoner Verification")
    print("=" * 60)

    print(f"Rank               : {result.rank}")
    print(f"Keep Highlight     : {result.keep_highlight}")
    print(f"Category           : {result.category}")
    print(f"Event Summary      : {result.event_summary}")
    print(
        f"Commentary Category: "
        f"{result.commentary_category}"
    )
    print(f"Visual Event       : {result.visual_event}")
    print(f"Action Level       : {result.action_level}")
    print(f"Danger Level       : {result.danger_level}")
    print(
        f"Final Confidence   : "
        f"{result.final_confidence:.4f}"
    )
    print(f"Reason             : {result.reason}")


if __name__ == "__main__":
    main()