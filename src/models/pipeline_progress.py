from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PipelineProgress:
    """Progress update emitted by the PressStartAI pipeline."""

    step: int
    total_steps: int
    message: str

    @property
    def percentage(self) -> float:
        if self.total_steps <= 0:
            return 0.0

        return (
            self.step
            / self.total_steps
        ) * 100.0