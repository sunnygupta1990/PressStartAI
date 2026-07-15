from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_score import HighlightScore


class HighlightSelector:
    """Select top-ranked highlight candidates."""

    def __init__(
        self,
        maximum_candidates: int = 5,
        minimum_score: float = 0.40,
        padding_before_seconds: float = 3.0,
        padding_after_seconds: float = 3.0,
    ) -> None:
        self.maximum_candidates = maximum_candidates
        self.minimum_score = minimum_score
        self.padding_before_seconds = padding_before_seconds
        self.padding_after_seconds = padding_after_seconds

    def select(
        self,
        scores: list[HighlightScore],
        video_duration_seconds: float,
    ) -> list[HighlightCandidate]:
        candidates: list[HighlightCandidate] = []

        eligible_scores = [
            score
            for score in scores
            if score.final_score >= self.minimum_score
        ]

        for rank, score in enumerate(
            eligible_scores[: self.maximum_candidates],
            start=1,
        ):
            features = score.features

            start_seconds = max(
                0.0,
                features.scene_start_seconds
                - self.padding_before_seconds,
            )

            end_seconds = min(
                video_duration_seconds,
                features.scene_end_seconds
                + self.padding_after_seconds,
            )

            candidates.append(
                HighlightCandidate(
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    rank=rank,
                    score=score,
                )
            )

        return candidates