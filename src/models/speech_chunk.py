from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SpeechChunk:
    """Speech audio chunk mapped to the original video timeline."""

    file_path: str
    start_seconds: float
    end_seconds: float