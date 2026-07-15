from src.models.final_highlight import FinalHighlight
from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_fusion import HighlightFusion


class FinalHighlightCombiner:
    """Link approved multimodal decisions to generated video clips."""

    def combine(
        self,
        highlights: list[GeneratedHighlight],
        approved_results: list[HighlightFusion],
    ) -> list[FinalHighlight]:
        highlights_by_rank = {
            highlight.rank: highlight
            for highlight in highlights
        }

        final_highlights: list[FinalHighlight] = []

        for result in approved_results:
            highlight = highlights_by_rank.get(
                result.rank
            )

            if highlight is None:
                continue

            final_highlights.append(
                FinalHighlight(
                    highlight=highlight,
                    fusion=result,
                )
            )

        return final_highlights