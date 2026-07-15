import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.exceptions.pipeline_execution_error import PipelineExecutionError
from src.services.pipeline_stage_runner import PipelineStageRunner


def failing_stage() -> None:
    raise ValueError("Verification failure")


def main() -> None:
    print("=" * 60)
    print("Pipeline Stage Runner Verification")
    print("=" * 60)

    runner = PipelineStageRunner()

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

        print("PipelineStageRunner verification successful.")
        return

    raise RuntimeError(
        "PipelineExecutionError was not raised."
    )


if __name__ == "__main__":
    main()