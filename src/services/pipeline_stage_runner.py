from collections.abc import Callable
from time import perf_counter
from typing import TypeVar

from src.exceptions.pipeline_execution_error import PipelineExecutionError
from src.models.pipeline_stage_timing import PipelineStageTiming


ResultType = TypeVar("ResultType")


class PipelineStageRunner:
    """Run pipeline stages with structured errors and timing."""

    def __init__(self) -> None:
        self.timings: list[PipelineStageTiming] = []

    def run(
        self,
        stage: str,
        action: Callable[[], ResultType],
    ) -> ResultType:
        start_time = perf_counter()

        try:
            return action()
        except PipelineExecutionError:
            raise
        except Exception as error:
            raise PipelineExecutionError(
                stage=stage,
                message=str(error),
            ) from error
        finally:
            duration_seconds = (
                perf_counter() - start_time
            )

            self.timings.append(
                PipelineStageTiming(
                    stage=stage,
                    duration_seconds=duration_seconds,
                )
            )