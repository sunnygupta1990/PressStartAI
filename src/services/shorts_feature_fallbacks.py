# src/services/shorts_feature_fallbacks.py

"""Deterministic fallbacks used when optional AI stages are disabled."""

from __future__ import annotations

from src.models.analyzed_highlight import AnalyzedHighlight
from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_fusion import HighlightFusion
from src.models.highlight_reasoning import HighlightReasoning
from src.models.visual_reasoning import VisualReasoning


class ShortsFeatureFallbacks:
    """Build compatible results without invoking disabled AI stages."""

    @staticmethod
    def commentary(
        highlights: list[GeneratedHighlight],
    ) -> list[HighlightReasoning]:
        """Use heuristic scores when commentary AI is disabled."""

        return [
            HighlightReasoning(
                rank=highlight.rank,
                is_interesting=True,
                category="heuristic",
                reason="Commentary AI disabled by configuration.",
                confidence=ShortsFeatureFallbacks._confidence(
                    highlight.final_score
                ),
            )
            for highlight in highlights
        ]

    @staticmethod
    def visual(
        highlights: list[GeneratedHighlight],
    ) -> dict[int, VisualReasoning]:
        """Use heuristic scores when visual AI is disabled."""

        return {
            highlight.rank: VisualReasoning(
                rank=highlight.rank,
                visual_event="",
                action_level="unknown",
                danger_level="unknown",
                looks_interesting=True,
                reason="Visual AI disabled by configuration.",
                confidence=ShortsFeatureFallbacks._confidence(
                    highlight.final_score
                ),
            )
            for highlight in highlights
        }

    @staticmethod
    def fusion(
        analyzed_highlights: list[AnalyzedHighlight],
        visual_results: dict[int, VisualReasoning],
    ) -> list[HighlightFusion]:
        """Combine available scores without invoking fusion AI."""

        results: list[HighlightFusion] = []

        for analyzed in analyzed_highlights:
            visual = visual_results.get(analyzed.rank)

            visual_confidence = (
                visual.confidence
                if visual is not None
                else analyzed.final_score
            )
            confidence = ShortsFeatureFallbacks._confidence(
                (
                    analyzed.confidence
                    + visual_confidence
                    + analyzed.final_score
                )
                / 3.0
            )

            results.append(
                HighlightFusion(
                    rank=analyzed.rank,
                    keep_highlight=True,
                    category=analyzed.category,
                    event_summary=analyzed.reason,
                    commentary_category=analyzed.category,
                    visual_event=(
                        visual.visual_event
                        if visual is not None
                        else ""
                    ),
                    action_level=(
                        visual.action_level
                        if visual is not None
                        else "unknown"
                    ),
                    danger_level=(
                        visual.danger_level
                        if visual is not None
                        else "unknown"
                    ),
                    final_confidence=confidence,
                    reason="Fusion AI disabled by configuration.",
                )
            )

        return results

    @staticmethod
    def _confidence(value: float) -> float:
        """Clamp a confidence score to the supported range."""

        return max(0.0, min(1.0, float(value)))
