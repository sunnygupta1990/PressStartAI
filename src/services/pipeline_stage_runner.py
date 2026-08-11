from collections.abc import Callable
from time import perf_counter
from typing import TypeVar

from src.exceptions.pipeline_execution_error import PipelineExecutionError
from src.models.pipeline_stage_timing import PipelineStageTiming
from src.services.checkpoint_cache import CheckpointCache


ResultType = TypeVar("ResultType")


class PipelineStageRunner:
    """Run pipeline stages with structured errors, timing, and safe cache reuse."""

    def __init__(
        self,
        checkpoint_cache: CheckpointCache | None = None,
    ) -> None:
        self.timings: list[PipelineStageTiming] = []
        self.checkpoint_cache = checkpoint_cache
        self.upstream_dirty = False

    def run(
        self,
        stage: str,
        action: Callable[[], ResultType],
        *,
        cacheable: bool = True,
    ) -> ResultType:
        start_time = perf_counter()
        cache_hit = False

        try:
            if (
                cacheable
                and self.checkpoint_cache is not None
                and not self.upstream_dirty
            ):
                cached = self.checkpoint_cache.load(stage)
                if cached.hit:
                    cache_hit = True
                    print(f"[CACHE] Reusing completed stage: {stage}")
                    return cached.value

            if cacheable:
                self.upstream_dirty = True

            if cacheable and self.checkpoint_cache is not None:
                self.checkpoint_cache.check_disk_safety()

            result = action()

            if cacheable and self.checkpoint_cache is not None:
                self.checkpoint_cache.check_disk_safety()
                self.checkpoint_cache.save(stage, result)
                print(f"[CHECKPOINT] Saved stage: {stage}")

            return result
        except PipelineExecutionError:
            raise
        except Exception as error:
            raise PipelineExecutionError(
                stage=stage,
                message=str(error),
            ) from error
        finally:
            duration_seconds = perf_counter() - start_time
            label = f"{stage} [cache]" if cache_hit else stage
            self.timings.append(
                PipelineStageTiming(
                    stage=label,
                    duration_seconds=duration_seconds,
                )
            )
