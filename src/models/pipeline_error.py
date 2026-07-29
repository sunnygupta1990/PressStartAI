from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PipelineError:
    """Structured error from a PressStartAI pipeline run."""

    stage: str
    message: str
    exception_type: str

    def __str__(self) -> str:
        return (
            f"{self.stage}: "
            f"{self.message} "
            f"({self.exception_type})"
        )