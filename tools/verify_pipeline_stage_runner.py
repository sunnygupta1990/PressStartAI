import sys
from pathlib import Path
from time import sleep

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.exceptions.pipeline_execution_error import PipelineExecutionError
from src.services.pipeline_stage_runner import PipelineStageRunner


def successful_stage() -> str:
    sleep(0.1)
    return "success"


def failing_stage() -> None:
    sleep(0.1)
    raise ValueError("Verification failure")


def main() -> None:
    print("=" * 60)
    print("Pipeline Stage Runner Verification")
    print("=" * 60)

    runner = PipelineStageRunner()

    result = runner.run(
        stage="Successful stage",
        action=successful_stage,
    )

    if result != "success":
        raise RuntimeError(
            "Successful stage returned an unexpected result."
        )

    try:
        runner.run(
            stage="Verification stage",
            action=failing_stage,
        )
    except PipelineExecutionError as error:
        print(f"Stage   : {error.stage}")
        print(f"Error   : {error}")

        if error.stage != "Verification stage":
            raise RuntimeError(
                "Pipeline stage name was not preserved."
            )
    else:
        raise RuntimeError(
            "PipelineExecutionError was not raised."
        )

    print()

    print(f"Timings Recorded : {len(runner.timings)}")

    for timing in runner.timings:
        print(
            f"{timing.stage} : "
            f"{timing.duration_seconds:.4f}s"
        )

    if len(runner.timings) != 2:
        raise RuntimeError(
            "Expected two recorded stage timings."
        )

    if any(
        timing.duration_seconds <= 0
        for timing in runner.timings
    ):
        raise RuntimeError(
            "Stage timing duration must be greater than zero."
        )

    print()
    print(
        "PipelineStageRunner timing verification successful."
    )


if __name__ == "__main__":
    main()