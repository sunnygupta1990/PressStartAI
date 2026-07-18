# src/services/final_highlight_selector.py

from src.models.highlight_fusion import HighlightFusion


class FinalHighlightSelector:
    """Rank every analyzed candidate without rejecting it."""

    def __init__(
        self,
        minimum_confidence: float = 0.0,
    ) -> None:
        """Preserve the existing constructor interface."""

        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between 0.0 and 1.0."
            )

        self.minimum_confidence = minimum_confidence

    def select(
        self,
        fusion_results: list[HighlightFusion],
    ) -> list[HighlightFusion]:
        """Return every candidate ranked by AI confidence."""

        return sorted(
            fusion_results,
            key=lambda result: (
                -result.final_confidence,
                result.rank,
            ),
        )