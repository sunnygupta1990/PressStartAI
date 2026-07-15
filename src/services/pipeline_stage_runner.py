from collections.abc import Callable
from typing import TypeVar

from src.exceptions.pipeline_execution_error import PipelineExecutionError


ResultType = TypeVar("ResultType")


class PipelineStageRunner:
    """Run one pipeline stage with structured error handling."""

    def run(
        self,
        stage: str,
        action: Callable[[], ResultType],
    ) -> ResultType:
        try:
            return action()
        except PipelineExecutionError:
            raise
        except Exception as error:
            raise PipelineExecutionError(
                stage=stage,
                message=str(error),
            ) from error