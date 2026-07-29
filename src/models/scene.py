from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Scene:
    """A detected scene mapped to the original video timeline."""

    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds