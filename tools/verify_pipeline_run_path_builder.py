import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.pipeline_run_path_builder import PipelineRunPathBuilder


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)


def main() -> None:
    print("=" * 60)
    print("Pipeline Run Path Builder Verification")
    print("=" * 60)

    builder = PipelineRunPathBuilder()

    first_run = builder.build(
        VIDEO_FILE
    )

    second_run = builder.build(
        VIDEO_FILE
    )

    print(f"First Run ID       : {first_run.run_id}")
    print(f"First Working      : {first_run.working_folder}")
    print(f"First Output       : {first_run.output_folder}")

    print()

    print(f"Second Run ID      : {second_run.run_id}")
    print(f"Second Working     : {second_run.working_folder}")
    print(f"Second Output      : {second_run.output_folder}")

    if first_run.run_id == second_run.run_id:
        raise RuntimeError(
            "Pipeline run IDs are not unique."
        )

    if first_run.working_folder == second_run.working_folder:
        raise RuntimeError(
            "Pipeline working folders are not unique."
        )

    if first_run.output_folder == second_run.output_folder:
        raise RuntimeError(
            "Pipeline output folders are not unique."
        )

    print()
    print(
        "PipelineRunPathBuilder verification successful."
    )


if __name__ == "__main__":
    main()