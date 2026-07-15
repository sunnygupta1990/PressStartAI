from src.models.highlight_candidate import HighlightCandidate


class HighlightOverlapResolver:
    """Remove lower-ranked highlight candidates that heavily overlap."""

    def __init__(
        self,
        maximum_overlap_ratio: float = 0.50,
    ) -> None:
        self.maximum_overlap_ratio = maximum_overlap_ratio

    def resolve(
        self,
        candidates: list[HighlightCandidate],
    ) -> list[HighlightCandidate]:
        resolved: list[HighlightCandidate] = []

        for candidate in candidates:
            has_excessive_overlap = any(
                self._calculate_overlap_ratio(
                    candidate,
                    selected,
                )
                > self.maximum_overlap_ratio
                for selected in resolved
            )

            if has_excessive_overlap:
                continue

            resolved.append(candidate)

        return resolved

    @staticmethod
    def _calculate_overlap_ratio(
        first: HighlightCandidate,
        second: HighlightCandidate,
    ) -> float:
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

        shorter_duration = min(
            first.duration_seconds,
            second.duration_seconds,
        )

        if shorter_duration <= 0:
            return 0.0

        return overlap_duration / shorter_duration