class PipelineExecutionError(RuntimeError):
    """Raised when a PressStartAI pipeline stage fails."""

    def __init__(
        self,
        stage: str,
        message: str,
    ) -> None:
        self.stage = stage

        super().__init__(
            f"{stage}: {message}"
        )