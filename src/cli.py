import argparse
from pathlib import Path

from src.models.pipeline_progress import PipelineProgress
from src.services.highlight_pipeline import HighlightPipeline


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the PressStartAI highlight pipeline "
            "for a gaming video."
        )
    )

    parser.add_argument(
        "video_file",
        help="Path to the source gaming video.",
    )

    parser.add_argument(
        "--working-folder",
        default="temp/pipeline_run",
        help="Folder used for temporary pipeline files.",
    )

    parser.add_argument(
        "--output-folder",
        default="output/highlights",
        help="Folder used for final approved highlights.",
    )

    return parser.parse_args()


def print_progress(
    progress: PipelineProgress,
) -> None:
    print(
        f"[{progress.step}/{progress.total_steps}] "
        f"{progress.message}..."
    )


def main() -> None:
    arguments = parse_arguments()

    video_file = Path(
        arguments.video_file
    )

    pipeline = HighlightPipeline()

    result = pipeline.run(
        video_file=str(video_file),
        working_folder=arguments.working_folder,
        output_folder=arguments.output_folder,
        progress_callback=print_progress,
    )

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

    for highlight, exported_file in zip(
        result.final_highlights,
        result.exported_files,
        strict=True,
    ):
        print()
        print("-" * 60)
        print(
            f"Rank             : "
            f"{highlight.rank}"
        )
        print(
            f"File             : "
            f"{exported_file}"
        )
        print(
            f"Category         : "
            f"{highlight.category}"
        )
        print(
            f"Confidence       : "
            f"{highlight.confidence:.4f}"
        )
        print(
            f"Event Summary    : "
            f"{highlight.event_summary}"
        )


if __name__ == "__main__":
    main()