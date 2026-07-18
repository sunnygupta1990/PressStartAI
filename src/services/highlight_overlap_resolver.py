# src/services/highlight_overlap_resolver.py

from src.models.highlight_candidate import HighlightCandidate


class HighlightOverlapResolver:
    """Keep overlapping highlights while removing near-duplicate candidates."""

    def __init__(
        self,
        minimum_duplicate_overlap_ratio: float = 0.90,
        maximum_boundary_difference_seconds: float = 5.0,
        maximum_primary_moment_difference_seconds: float = 3.0,
    ) -> None:
        if not 0.0 <= minimum_duplicate_overlap_ratio <= 1.0:
            raise ValueError(
                "minimum_duplicate_overlap_ratio must be between "
                "0.0 and 1.0."
            )

        if maximum_boundary_difference_seconds < 0:
            raise ValueError(
                "maximum_boundary_difference_seconds cannot be negative."
            )

        if maximum_primary_moment_difference_seconds < 0:
            raise ValueError(
                "maximum_primary_moment_difference_seconds "
                "cannot be negative."
            )

        self.minimum_duplicate_overlap_ratio = (
            minimum_duplicate_overlap_ratio
        )
        self.maximum_boundary_difference_seconds = (
            maximum_boundary_difference_seconds
        )
        self.maximum_primary_moment_difference_seconds = (
            maximum_primary_moment_difference_seconds
        )

    def resolve(
        self,
        candidates: list[HighlightCandidate],
    ) -> list[HighlightCandidate]:
        """Return all candidates except genuine near-duplicates."""

        resolved: list[HighlightCandidate] = []

        for candidate in candidates:
            is_duplicate = any(
                self._is_near_duplicate(
                    candidate,
                    selected,
                )
                for selected in resolved
            )

            if not is_duplicate:
                resolved.append(candidate)

        return resolved

    def _is_near_duplicate(
        self,
        first: HighlightCandidate,
        second: HighlightCandidate,
    ) -> bool:
        """Determine whether two candidates represent the same moment."""

        overlap_ratio = self._calculate_intersection_over_union(
            first,
            second,
        )

        if (
            overlap_ratio
            < self.minimum_duplicate_overlap_ratio
        ):
            return False

        start_difference = abs(
            first.start_seconds
            - second.start_seconds
        )
        end_difference = abs(
            first.end_seconds
            - second.end_seconds
        )

        if (
            start_difference
            > self.maximum_boundary_difference_seconds
            or end_difference
            > self.maximum_boundary_difference_seconds
        ):
            return False

        first_primary_moment = self._primary_moment(first)
        second_primary_moment = self._primary_moment(second)

        primary_moment_difference = abs(
            first_primary_moment
            - second_primary_moment
        )

        return (
            primary_moment_difference
            <= self.maximum_primary_moment_difference_seconds
        )

    @staticmethod
    def _primary_moment(
        candidate: HighlightCandidate,
    ) -> float:
        """Return the midpoint of the scene that created the candidate."""

        features = candidate.score.features

        return (
            features.scene_start_seconds
            + features.scene_end_seconds
        ) / 2.0

    @staticmethod
    def _calculate_intersection_over_union(
        first: HighlightCandidate,
        second: HighlightCandidate,
    ) -> float:
        """Calculate temporal intersection over union."""

        overlap_start = max(
            first.start_seconds,
            second.start_seconds,
        )
        overlap_end = min(
            first.end_seconds,
            second.end_seconds,
        )

        overlap_duration = max(
            0.0,
            overlap_end - overlap_start,
        )

        union_start = min(
            first.start_seconds,
            second.start_seconds,
        )
        union_end = max(
            first.end_seconds,
            second.end_seconds,
        )
        union_duration = max(
            0.0,
            union_end - union_start,
        )

        if union_duration <= 0:
            return 0.0

        return overlap_duration / union_duration
