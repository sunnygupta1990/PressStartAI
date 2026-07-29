from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ASRSegment:
    """Transcribed speech mapped to the original video timeline."""

    start_seconds: float
    end_seconds: float
    language: str
    text: str