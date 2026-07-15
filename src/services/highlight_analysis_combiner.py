from src.models.analyzed_highlight import AnalyzedHighlight
from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_reasoning import HighlightReasoning


class HighlightAnalysisCombiner:
    """Combine generated highlights with matching AI reasoning."""

    def combine(
        self,
        highlights: list[GeneratedHighlight],
        reasoning_results: list[HighlightReasoning],
    ) -> list[AnalyzedHighlight]:
        reasoning_by_rank = {
            result.rank: result
            for result in reasoning_results
        }

        analyzed: list[AnalyzedHighlight] = []

        for highlight in highlights:
            reasoning = reasoning_by_rank.get(
                highlight.rank
            )

            if reasoning is None:
                continue

            analyzed.append(
                AnalyzedHighlight(
                    highlight=highlight,
                    reasoning=reasoning,
                )
            )

        return analyzed