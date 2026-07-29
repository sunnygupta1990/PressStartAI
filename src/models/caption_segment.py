from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CaptionSegment:
    """One timed caption segment for a rendered Short."""

    start_seconds: float
    end_seconds: float
    text: str

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds