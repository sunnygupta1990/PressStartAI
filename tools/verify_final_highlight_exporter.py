import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.final_highlight import FinalHighlight
from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_fusion import HighlightFusion
from src.models.highlight_score import HighlightScore
from src.services.final_highlight_exporter import FinalHighlightExporter


OUTPUT_FOLDER = "output/highlights"


def create_final_highlight(
    file_path: str,
    rank: int,
    start_seconds: float,
    end_seconds: float,
    final_score: float,
    transcript_text: str,
    category: str,
    event_summary: str,
    commentary_category: str,
    visual_event: str,
    action_level: str,
    danger_level: str,
    confidence: float,
    reason: str,
) -> FinalHighlight:
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

    generated_highlight = GeneratedHighlight(
        file_path=file_path,
        candidate=candidate,
    )

    fusion = HighlightFusion(
        rank=rank,
        keep_highlight=True,
        category=category,
        event_summary=event_summary,
        commentary_category=commentary_category,
        visual_event=visual_event,
        action_level=action_level,
        danger_level=danger_level,
        final_confidence=confidence,
        reason=reason,
    )

    return FinalHighlight(
        highlight=generated_highlight,
        fusion=fusion,
    )


def main() -> None:
    highlights = [
        create_final_highlight(
            file_path=(
                r"temp\final_highlights\highlight_001.mp4"
            ),
            rank=1,
            start_seconds=18.00,
            end_seconds=29.17,
            final_score=0.8342,
            transcript_text=(
                "बाग बाग बाग बाग गलत हक्किया चलो "
                "उस पेल ने बचा लिया मेरे को कभी नहीं हाँ"
            ),
            category="reaction",
            event_summary=(
                "Strong boss-fight reaction."
            ),
            commentary_category="reaction",
            visual_event=(
                "Player fighting a dangerous enemy."
            ),
            action_level="high",
            danger_level="high",
            confidence=0.95,
            reason=(
                "Strong multimodal reaction highlight."
            ),
        ),
        create_final_highlight(
            file_path=(
                r"temp\final_highlights\highlight_002.mp4"
            ),
            rank=4,
            start_seconds=0.00,
            end_seconds=12.17,
            final_score=0.4806,
            transcript_text=(
                "जो आती गलत हो गई हर इससे सामने"
            ),
            category="rage",
            event_summary=(
                "Strong frustrated combat moment."
            ),
            commentary_category="rage",
            visual_event=(
                "Player fighting multiple enemies."
            ),
            action_level="high",
            danger_level="high",
            confidence=0.93,
            reason=(
                "Strong multimodal rage highlight."
            ),
        ),
    ]

    exporter = FinalHighlightExporter()

    exported_files = exporter.export(
        highlights=highlights,
        output_folder=OUTPUT_FOLDER,
    )

    print("=" * 60)
    print("Final Highlight Exporter Verification")
    print("=" * 60)

    print(
        f"Exported Highlights: "
        f"{len(exported_files)}"
    )
    print()

    for exported_file in exported_files:
        clip_path = Path(exported_file)

        metadata_path = (
            Path(OUTPUT_FOLDER)
            / "metadata"
            / f"{clip_path.stem}.json"
        )

        print("-" * 60)
        print(f"Clip           : {clip_path}")
        print(
            f"Clip Exists    : "
            f"{clip_path.is_file()}"
        )

        if clip_path.is_file():
            print(
                f"Clip Size      : "
                f"{clip_path.stat().st_size / 1024 / 1024:.2f} MB"
            )

        print(
            f"Metadata       : "
            f"{metadata_path}"
        )
        print(
            f"Metadata Exists: "
            f"{metadata_path.is_file()}"
        )

        if metadata_path.is_file():
            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            print(
                f"Category       : "
                f"{metadata.get('category')}"
            )
            print(
                f"Confidence     : "
                f"{metadata.get('confidence')}"
            )
            print(
                f"Summary        : "
                f"{metadata.get('event_summary')}"
            )


if __name__ == "__main__":
    main()