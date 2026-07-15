from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PipelineStageTiming:
    """Execution timing for one PressStartAI pipeline stage."""

    stage: str
    duration_seconds: float