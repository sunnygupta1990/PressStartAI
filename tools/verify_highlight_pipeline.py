import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.highlight_pipeline import HighlightPipeline


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)

WORKING_FOLDER = "temp/pipeline_run"
OUTPUT_FOLDER = "output/pipeline_highlights"


def main() -> None:
    print("=" * 60)
    print("Highlight Pipeline Verification")
    print("=" * 60)

    pipeline = HighlightPipeline()

    result = pipeline.run(
        video_file=VIDEO_FILE,
        working_folder=WORKING_FOLDER,
        output_folder=OUTPUT_FOLDER,
    )

    print()
    print("=" * 60)
    print("PIPELINE RESULT")
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
        print(f"Rank             : {highlight.rank}")
        print(f"File             : {exported_file}")
        print(f"Category         : {highlight.category}")
        print(
            f"Confidence       : "
            f"{highlight.confidence:.4f}"
        )
        print(
            f"Event Summary    : "
            f"{highlight.event_summary}"
        )
        print(
            f"Source Timeline  : "
            f"{highlight.start_seconds:.2f}s "
            f"-> {highlight.end_seconds:.2f}s"
        )


if __name__ == "__main__":
    main()