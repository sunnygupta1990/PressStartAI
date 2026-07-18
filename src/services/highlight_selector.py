# src/services/highlight_selector.py

from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_score import HighlightScore


class HighlightSelector:
    """Create every eligible highlight candidate within duration limits."""

    def __init__(
        self,
        minimum_score: float = 0.40,
        minimum_highlight_duration_seconds: float = 45.0,
        maximum_highlight_duration_seconds: float = 145.0,
    ) -> None:
        if not 0.0 <= minimum_score <= 1.0:
            raise ValueError(
                "minimum_score must be between 0.0 and 1.0."
            )

        if minimum_highlight_duration_seconds <= 0:
            raise ValueError(
                "minimum_highlight_duration_seconds must be positive."
            )

        if (
            maximum_highlight_duration_seconds
            < minimum_highlight_duration_seconds
        ):
            raise ValueError(
                "maximum_highlight_duration_seconds must be greater "
                "than or equal to minimum_highlight_duration_seconds."
            )

        self.minimum_score = minimum_score
        self.minimum_highlight_duration_seconds = (
            minimum_highlight_duration_seconds
        )
        self.maximum_highlight_duration_seconds = (
            maximum_highlight_duration_seconds
        )

    def select(
        self,
        scores: list[HighlightScore],
        video_duration_seconds: float,
    ) -> list[HighlightCandidate]:
        """Return every eligible candidate ordered by heuristic rank."""

        if video_duration_seconds <= 0:
            raise ValueError(
                "video_duration_seconds must be positive."
            )

        eligible_scores = [
            score
            for score in scores
            if score.final_score >= self.minimum_score
        ]

        candidates: list[HighlightCandidate] = []

        for rank, score in enumerate(
            eligible_scores,
            start=1,
        ):
            start_seconds, end_seconds = self._build_time_window(
                scene_start_seconds=(
                    score.features.scene_start_seconds
                ),
                scene_end_seconds=(
                    score.features.scene_end_seconds
                ),
                video_duration_seconds=video_duration_seconds,
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

    def _build_time_window(
        self,
        scene_start_seconds: float,
        scene_end_seconds: float,
        video_duration_seconds: float,
    ) -> tuple[float, float]:
        """Build a valid 45–145 second window around one scene."""

        scene_start = max(
            0.0,
            min(
                scene_start_seconds,
                video_duration_seconds,
            ),
        )
        scene_end = max(
            scene_start,
            min(
                scene_end_seconds,
                video_duration_seconds,
            ),
        )

        available_duration = min(
            self.maximum_highlight_duration_seconds,
            video_duration_seconds,
        )

        target_duration = max(
            self.minimum_highlight_duration_seconds,
            scene_end - scene_start,
        )
        target_duration = min(
            target_duration,
            available_duration,
        )

        scene_midpoint = (
            scene_start + scene_end
        ) / 2.0

        start_seconds = (
            scene_midpoint - target_duration / 2.0
        )
        end_seconds = (
            start_seconds + target_duration
        )

        if start_seconds < 0.0:
            start_seconds = 0.0
            end_seconds = target_duration

        if end_seconds > video_duration_seconds:
            end_seconds = video_duration_seconds
            start_seconds = max(
                0.0,
                end_seconds - target_duration,
            )

        return (
            start_seconds,
            end_seconds,
        )
