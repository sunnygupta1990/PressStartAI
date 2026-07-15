import argparse
from pathlib import Path

from src.exceptions.pipeline_execution_error import PipelineExecutionError
from src.models.pipeline_error import PipelineError
from src.models.pipeline_progress import PipelineProgress
from src.services.highlight_pipeline import HighlightPipeline
from src.services.pipeline_run_path_builder import PipelineRunPathBuilder


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the PressStartAI highlight and YouTube Short pipeline "
            "for a gaming video."
        )
    )

    parser.add_argument(
        "video_file",
        help="Path to the source gaming video.",
    )

    parser.add_argument(
        "--working-folder",
        default=None,
        help=(
            "Optional folder used for temporary pipeline files. "
            "A unique run folder is created by default."
        ),
    )

    parser.add_argument(
        "--output-folder",
        default=None,
        help=(
            "Optional folder used for final pipeline outputs. "
            "A unique run folder is created by default."
        ),
    )

    return parser.parse_args()


def print_progress(
    progress: PipelineProgress,
) -> None:
    print(
        f"[{progress.step}/{progress.total_steps}] "
        f"{progress.message}..."
    )


def print_pipeline_error(
    error: PipelineError,
) -> None:
    print()
    print("=" * 60)
    print("PRESSSTARTAI ERROR")
    print("=" * 60)
    print(f"Stage            : {error.stage}")
    print(f"Error            : {error.message}")
    print(f"Exception Type   : {error.exception_type}")


def main() -> None:
    arguments = parse_arguments()

    video_file = Path(
        arguments.video_file
    )

    path_builder = PipelineRunPathBuilder()

    run_paths = path_builder.build(
        video_file=str(video_file),
    )

    working_folder = (
        arguments.working_folder
        or run_paths.working_folder
    )

    output_folder = (
        arguments.output_folder
        or run_paths.output_folder
    )

    print("=" * 60)
    print("PRESSSTARTAI")
    print("=" * 60)
    print(f"Run ID            : {run_paths.run_id}")
    print(f"Working Folder    : {working_folder}")
    print(f"Output Folder     : {output_folder}")
    print()

    pipeline = HighlightPipeline()

    try:
        result = pipeline.run(
            video_file=str(video_file),
            working_folder=working_folder,
            output_folder=output_folder,
            progress_callback=print_progress,
        )
    except PipelineExecutionError as error:
        pipeline_error = PipelineError(
            stage=error.stage,
            message=str(error.__cause__ or error),
            exception_type=type(
                error.__cause__ or error
            ).__name__,
        )

        print_pipeline_error(
            pipeline_error
        )

        return
    except Exception as error:
        pipeline_error = PipelineError(
            stage="Starting pipeline",
            message=str(error),
            exception_type=type(error).__name__,
        )

        print_pipeline_error(
            pipeline_error
        )

        return

    print()
    print("=" * 60)
    print("PRESSSTARTAI RESULT")
    print("=" * 60)

    print(
        f"Source Video      : "
        f"{result.source_video_file}"
    )

    print(
        f"Video Duration    : "
        f"{result.video_duration_seconds:.2f}s"
    )

    print(
        f"Final Highlights  : "
        f"{result.highlight_count}"
    )

    print(
        f"Exported Files    : "
        f"{result.exported_file_count}"
    )

    print(
        f"Short Packages    : "
        f"{result.short_package_count}"
    )

    print(
        f"Pipeline Time     : "
        f"{result.total_duration_seconds:.2f}s"
    )

    print(
        f"Output Folder     : "
        f"{output_folder}"
    )

    for package in result.short_packages:
        print()
        print("-" * 60)
        print(
            f"Rank             : "
            f"{package.rank}"
        )
        print(
            f"Final Short      : "
            f"{package.final_video_file}"
        )
        print(
            f"Captions         : "
            f"{package.subtitle_file}"
        )
        print(
            f"Category         : "
            f"{package.category}"
        )
        print(
            f"Confidence       : "
            f"{package.confidence:.4f}"
        )
        print(
            f"Hook             : "
            f"{package.metadata.hook}"
        )
        print(
            f"Title            : "
            f"{package.metadata.title}"
        )
        print(
            f"Description      : "
            f"{package.metadata.description}"
        )
        print(
            f"Hashtags         : "
            f"{' '.join(package.metadata.hashtags)}"
        )
        print(
            f"Thumbnail Prompt : "
            f"{package.metadata.thumbnail_prompt}"
        )

    print()
    print("=" * 60)
    print("PIPELINE STAGE TIMINGS")
    print("=" * 60)

    for timing in result.stage_timings:
        print(
            f"{timing.stage:<45} "
            f"{timing.duration_seconds:.2f}s"
        )


if __name__ == "__main__":
    main()