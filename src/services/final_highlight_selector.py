from src.models.highlight_fusion import HighlightFusion


class FinalHighlightSelector:
    """Select final highlights approved by multimodal AI."""

    def __init__(
        self,
        minimum_confidence: float = 0.70,
    ) -> None:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be "
                "between 0.0 and 1.0"
            )

        self.minimum_confidence = minimum_confidence

    def select(
        self,
        fusion_results: list[HighlightFusion],
    ) -> list[HighlightFusion]:
        selected = [
            result
            for result in fusion_results
            if (
                result.keep_highlight
                and result.final_confidence
                >= self.minimum_confidence
            )
        ]

        return sorted(
            selected,
            key=lambda result: (
                -result.final_confidence,
                result.rank,
            ),
        )