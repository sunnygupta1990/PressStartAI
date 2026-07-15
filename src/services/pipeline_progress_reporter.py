from collections.abc import Callable

from src.models.pipeline_progress import PipelineProgress


PipelineProgressCallback = Callable[
    [PipelineProgress],
    None,
]


class PipelineProgressReporter:
    """Emit progress updates for a PressStartAI pipeline run."""

    def __init__(
        self,
        callback: PipelineProgressCallback | None = None,
        total_steps: int = 19,
    ) -> None:
        self.callback = callback
        self.total_steps = total_steps

    def report(
        self,
        step: int,
        message: str,
    ) -> PipelineProgress:
        progress = PipelineProgress(
            step=step,
            total_steps=self.total_steps,
            message=message,
        )

        if self.callback is not None:
            self.callback(progress)

        return progress