import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.highlight_fusion import HighlightFusion
from src.services.final_highlight_selector import FinalHighlightSelector


def main() -> None:
    fusion_results = [
        HighlightFusion(
            rank=1,
            keep_highlight=True,
            category="combat",
            event_summary="High-intensity combat encounter.",
            commentary_category="reaction",
            visual_event="Player fighting a dangerous enemy.",
            action_level="high",
            danger_level="high",
            final_confidence=0.93,
            reason="Strong multimodal highlight.",
        ),
        HighlightFusion(
            rank=2,
            keep_highlight=False,
            category="unknown",
            event_summary="Low-interest movement.",
            commentary_category="unknown",
            visual_event="Player walking through an empty area.",
            action_level="low",
            danger_level="low",
            final_confidence=0.88,
            reason="Not interesting enough.",
        ),
        HighlightFusion(
            rank=3,
            keep_highlight=True,
            category="reaction",
            event_summary="Weak reaction moment.",
            commentary_category="reaction",
            visual_event="Minor gameplay event.",
            action_level="low",
            danger_level="low",
            final_confidence=0.60,
            reason="Confidence is below the final threshold.",
        ),
        HighlightFusion(
            rank=4,
            keep_highlight=True,
            category="rage",
            event_summary="Strong frustrated gameplay reaction.",
            commentary_category="rage",
            visual_event="Intense combat with multiple enemies.",
            action_level="high",
            danger_level="high",
            final_confidence=0.90,
            reason="Strong rage highlight.",
        ),
    ]

    selector = FinalHighlightSelector(
        minimum_confidence=0.70,
    )

    selected = selector.select(
        fusion_results
    )

    print("=" * 60)
    print("Final Highlight Selector Verification")
    print("=" * 60)

    print(f"Input Results      : {len(fusion_results)}")
    print(f"Selected Highlights: {len(selected)}")
    print()

    for result in selected:
        print("-" * 60)
        print(f"Rank       : {result.rank}")
        print(f"Keep       : {result.keep_highlight}")
        print(f"Category   : {result.category}")
        print(
            f"Confidence : "
            f"{result.final_confidence:.4f}"
        )
        print(
            f"Summary    : "
            f"{result.event_summary}"
        )


if __name__ == "__main__":
    main()