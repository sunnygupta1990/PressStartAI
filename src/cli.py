# src/cli.py

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

from src.exceptions.pipeline_execution_error import PipelineExecutionError
from src.models.pipeline_error import PipelineError
from src.models.pipeline_progress import PipelineProgress
from src.services.highlight_pipeline import HighlightPipeline
from src.services.pipeline_run_path_builder import PipelineRunPathBuilder
from src.services.ranking_video_cli import (
    create_ranking_video_from_dialogs,
)


@dataclass(slots=True)
class SelectedRecordings:
    """Files selected for one pipeline run."""

    normal_recording: str
    gameplay_recording: str | None = None
    facecam_recording: str | None = None

    @property
    def is_facecam_mode(self) -> bool:
        return bool(
            self.gameplay_recording
            and self.facecam_recording
        )


def parse_arguments() -> argparse.Namespace:
    """Parse optional output-location overrides."""

    parser = argparse.ArgumentParser(
        description="Run the PressStartAI desktop-style pipeline menu."
    )

    parser.add_argument(
        "--working-folder",
        default=None,
        help="Optional folder used for temporary pipeline files.",
    )

    parser.add_argument(
        "--output-folder",
        default=None,
        help="Optional folder used for final pipeline outputs.",
    )

    return parser.parse_args()


def print_progress(progress: PipelineProgress) -> None:
    """Print pipeline progress."""

    print(
        f"[{progress.step}/{progress.total_steps}] "
        f"{progress.message}..."
    )


def print_pipeline_error(error: PipelineError) -> None:
    """Print a readable pipeline error."""

    print()
    print("=" * 60)
    print("PRESSSTARTAI ERROR")
    print("=" * 60)
    print(f"Stage            : {error.stage}")
    print(f"Error            : {error.message}")
    print(f"Exception Type   : {error.exception_type}")


def select_mp4_file(
    title: str,
    excluded_paths: set[Path] | None = None,
) -> str | None:
    """Open a Windows file-selection dialog for one unique MP4 file."""

    excluded = excluded_paths or set()

    while True:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        selected_file = filedialog.askopenfilename(
            parent=root,
            title=title,
            filetypes=[
                ("MP4 video files", "*.mp4"),
            ],
        )

        root.destroy()

        if not selected_file:
            return None

        selected_path = Path(selected_file).resolve()

        if selected_path in excluded:
            message_root = tk.Tk()
            message_root.withdraw()
            message_root.attributes("-topmost", True)

            messagebox.showerror(
                "Duplicate Recording",
                (
                    "This file has already been selected for another "
                    "recording role.\n\nPlease select a different MP4 file."
                ),
                parent=message_root,
            )

            message_root.destroy()
            continue

        return str(selected_path)


def select_background_removal_output(
    source_video: str,
) -> str | None:
    """Select where the background-removed MP4 should be saved."""

    source_path = Path(source_video)
    default_name = (
        f"{source_path.stem}_background_removed.mp4"
    )

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    selected_file = filedialog.asksaveasfilename(
        parent=root,
        title="Save Background-Removed Video",
        initialdir=str(source_path.parent),
        initialfile=default_name,
        defaultextension=".mp4",
        filetypes=[
            ("MP4 video files", "*.mp4"),
        ],
    )

    root.destroy()

    if not selected_file:
        return None

    return str(Path(selected_file).resolve())


def create_black_background(
    width: int,
    height: int,
) -> object:
    """Create the replacement background used by the MP4 output."""

    import numpy as np

    return np.zeros(
        (height, width, 3),
        dtype=np.uint8,
    )


def remux_original_audio(
    silent_video: Path,
    source_video: Path,
    output_video: Path,
) -> bool:
    """Copy source audio into the processed video when FFmpeg is available."""

    ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path is None:
        return False

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(silent_video),
        "-i",
        str(source_video),
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_video),
    ]

    completed_process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    return (
        completed_process.returncode == 0
        and output_video.exists()
        and output_video.stat().st_size > 0
    )


def remove_video_background() -> None:
    """Run standalone facecam background removal from the main menu."""

    source_video = select_mp4_file(
        "Select Video for Background Removal",
    )

    if source_video is None:
        return

    output_video = select_background_removal_output(
        source_video
    )

    if output_video is None:
        return

    try:
        import cv2

        from src.services.facecam_background_removal_service import (
            RvmOpenVinoMattingService,
        )
    except ImportError as error:
        print()
        print(
            "Background removal dependencies are unavailable: "
            f"{error}"
        )
        return

    source_path = Path(source_video).resolve()
    output_path = Path(output_video).resolve()
    model_path = Path(
        "models/rvm/rvm_mobilenetv3_fp16.onnx"
    ).resolve()

    if source_path == output_path:
        print(
            "The output file must be different from the input file."
        )
        return

    if not model_path.exists():
        print(
            "Background-removal model was not found: "
            f"{model_path}"
        )
        return

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    silent_output_path = output_path.with_name(
        f"{output_path.stem}.silent{output_path.suffix}"
    )

    capture = cv2.VideoCapture(str(source_path))
    writer = None

    try:
        if not capture.isOpened():
            raise RuntimeError(
                f"Unable to open video: {source_path}"
            )

        fps = float(
            capture.get(cv2.CAP_PROP_FPS)
        )
        width = int(
            capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        )
        height = int(
            capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )
        frame_count = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if fps <= 0 or width <= 0 or height <= 0:
            raise RuntimeError(
                "Unable to read the source video metadata."
            )

        writer = cv2.VideoWriter(
            str(silent_output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        if not writer.isOpened():
            raise RuntimeError(
                f"Unable to create output video: "
                f"{silent_output_path}"
            )

        service = RvmOpenVinoMattingService(
            model_path=model_path,
            device="CPU",
            downsample_ratio=0.25,
            alpha_threshold=0.02,
            maximum_processing_width=1280,
        )
        service.reset()

        replacement_background = create_black_background(
            width=width,
            height=height,
        )

        processed_frames = 0
        progress_interval = max(
            1,
            round(fps),
        )

        print()
        print("=" * 60)
        print("REMOVE VIDEO BACKGROUND")
        print("=" * 60)
        print(f"Input  : {source_path}")
        print(f"Output : {output_path}")
        print()

        while True:
            success, frame = capture.read()

            if not success or frame is None:
                break

            result = service.process_frame(frame)
            processed_frame = result.composite_over(
                replacement_background
            )

            writer.write(processed_frame)
            processed_frames += 1

            if (
                processed_frames == 1
                or processed_frames % progress_interval == 0
            ):
                if frame_count > 0:
                    percentage = min(
                        100.0,
                        processed_frames
                        / frame_count
                        * 100.0,
                    )
                    print(
                        f"Processed {processed_frames}/"
                        f"{frame_count} frames "
                        f"({percentage:.1f}%)"
                    )
                else:
                    print(
                        f"Processed {processed_frames} frames"
                    )

        if processed_frames == 0:
            raise RuntimeError(
                "No video frames were processed."
            )

    except Exception as error:
        print()
        print(
            "Background removal failed: "
            f"{error}"
        )
        return
    finally:
        capture.release()

        if writer is not None:
            writer.release()

    audio_was_added = remux_original_audio(
        silent_video=silent_output_path,
        source_video=source_path,
        output_video=output_path,
    )

    if audio_was_added:
        silent_output_path.unlink(
            missing_ok=True,
        )
    else:
        if output_path.exists():
            output_path.unlink()

        silent_output_path.replace(output_path)

    print()
    print("=" * 60)
    print("BACKGROUND REMOVAL COMPLETE")
    print("=" * 60)
    print(f"Output : {output_path}")
    print(
        "Audio  : "
        + (
            "Original audio preserved"
            if audio_was_added
            else "No audio copied because FFmpeg was unavailable"
        )
    )



def select_normal_mode_files() -> SelectedRecordings | None:
    """Select the recording required for Normal Mode."""

    normal_recording = select_mp4_file(
        "Select Normal Recording",
    )

    if normal_recording is None:
        return None

    selections = SelectedRecordings(
        normal_recording=normal_recording,
    )

    return confirm_normal_mode_files(selections)


def select_facecam_mode_files() -> SelectedRecordings | None:
    """Select all recordings required for Facecam Mode."""

    normal_recording = select_mp4_file(
        "Select Normal Combined Recording",
    )

    if normal_recording is None:
        return None

    gameplay_recording = select_mp4_file(
        "Select Gameplay Recording",
        excluded_paths={
            Path(normal_recording).resolve(),
        },
    )

    if gameplay_recording is None:
        return None

    facecam_recording = select_mp4_file(
        "Select Facecam Recording",
        excluded_paths={
            Path(normal_recording).resolve(),
            Path(gameplay_recording).resolve(),
        },
    )

    if facecam_recording is None:
        return None

    selections = SelectedRecordings(
        normal_recording=normal_recording,
        gameplay_recording=gameplay_recording,
        facecam_recording=facecam_recording,
    )

    return confirm_facecam_mode_files(selections)


def confirm_normal_mode_files(
    selections: SelectedRecordings,
) -> SelectedRecordings | None:
    """Confirm or replace the Normal Mode recording."""

    while True:
        print()
        print("=" * 60)
        print("CONFIRM SELECTED FILE")
        print("=" * 60)
        print()
        print("Normal Recording")
        print(selections.normal_recording)
        print()
        print("-" * 60)
        print("1. Replace Normal Recording")
        print("2. Start Processing")
        print("3. Return to Main Menu")
        print("-" * 60)

        choice = input("Select an option: ").strip()

        if choice == "1":
            replacement = select_mp4_file(
                "Replace Normal Recording",
            )

            if replacement is None:
                return None

            selections.normal_recording = replacement
            continue

        if choice == "2":
            return selections

        if choice == "3":
            return None

        print("Please enter 1, 2, or 3.")


def confirm_facecam_mode_files(
    selections: SelectedRecordings,
) -> SelectedRecordings | None:
    """Confirm or replace Facecam Mode recordings."""

    while True:
        print()
        print("=" * 60)
        print("CONFIRM SELECTED FILES")
        print("=" * 60)
        print()
        print("1. Normal Recording")
        print(f"   {selections.normal_recording}")
        print()
        print("2. Gameplay Recording")
        print(f"   {selections.gameplay_recording}")
        print()
        print("3. Facecam Recording")
        print(f"   {selections.facecam_recording}")
        print()
        print("-" * 60)
        print("1. Replace Normal Recording")
        print("2. Replace Gameplay Recording")
        print("3. Replace Facecam Recording")
        print("4. Start Processing")
        print("5. Return to Main Menu")
        print("-" * 60)

        choice = input("Select an option: ").strip()

        if choice == "1":
            replacement = select_mp4_file(
                "Replace Normal Recording",
                excluded_paths={
                    Path(selections.gameplay_recording or "").resolve(),
                    Path(selections.facecam_recording or "").resolve(),
                },
            )

            if replacement is None:
                return None

            selections.normal_recording = replacement
            continue

        if choice == "2":
            replacement = select_mp4_file(
                "Replace Gameplay Recording",
                excluded_paths={
                    Path(selections.normal_recording).resolve(),
                    Path(selections.facecam_recording or "").resolve(),
                },
            )

            if replacement is None:
                return None

            selections.gameplay_recording = replacement
            continue

        if choice == "3":
            replacement = select_mp4_file(
                "Replace Facecam Recording",
                excluded_paths={
                    Path(selections.normal_recording).resolve(),
                    Path(selections.gameplay_recording or "").resolve(),
                },
            )

            if replacement is None:
                return None

            selections.facecam_recording = replacement
            continue

        if choice == "4":
            return selections

        if choice == "5":
            return None

        print("Please enter a number from 1 to 5.")



def display_main_menu() -> str:
    """Display the main processing-mode menu."""

    print()
    print("=" * 60)
    print("PRESSSTARTAI v1.0")
    print("=" * 60)
    print()
    print("Select Processing Mode")
    print()
    print("1. Normal Mode")
    print("   Single gameplay recording")
    print()
    print("2. Facecam Mode")
    print("   Combined + Gameplay + Facecam")
    print()
    print("3. Remove Video Background")
    print("   Select a video using a file dialog")
    print()
    print("4. Exit")
    print()
    print("5. Create Ranking Video")
    print("   Select multiple clips and assign ranks")
    print()
    print("-" * 60)

    return input("Enter your choice: ").strip()


def run_pipeline(
    selections: SelectedRecordings,
    arguments: argparse.Namespace,
) -> None:
    """Run one confirmed PressStartAI processing session."""

    layout_type = (
        "face_top"
        if selections.is_facecam_mode
        else "portrait"
    )

    path_builder = PipelineRunPathBuilder()

    run_paths = path_builder.build(
        video_file=selections.normal_recording,
    )

    working_folder = (
        arguments.working_folder
        or run_paths.working_folder
    )

    output_folder = (
        arguments.output_folder
        or run_paths.output_folder
    )

    layout_name = (
        "Face camera on top Short"
        if layout_type == "face_top"
        else "Normal portrait Short"
    )

    print()
    print("=" * 60)
    print("PRESSSTARTAI")
    print("=" * 60)
    print(f"Run ID            : {run_paths.run_id}")
    print(f"Normal Recording  : {selections.normal_recording}")

    if selections.gameplay_recording:
        print(
            f"Gameplay Recording: "
            f"{selections.gameplay_recording}"
        )

    if selections.facecam_recording:
        print(
            f"Facecam Recording : "
            f"{selections.facecam_recording}"
        )

    print(f"Working Folder    : {working_folder}")
    print(f"Output Folder     : {output_folder}")
    print(f"Short Layout      : {layout_name}")
    print()

    pipeline = HighlightPipeline()

    try:
        result = pipeline.run(
            video_file=selections.normal_recording,
            working_folder=working_folder,
            output_folder=output_folder,
            layout_type=layout_type,
            gameplay_video=selections.gameplay_recording,
            facecam_video=selections.facecam_recording,
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

        print_pipeline_error(pipeline_error)
        return
    except Exception as error:
        pipeline_error = PipelineError(
            stage="Starting pipeline",
            message=str(error),
            exception_type=type(error).__name__,
        )

        print_pipeline_error(pipeline_error)
        return

    print_pipeline_result(
        result=result,
        output_folder=output_folder,
    )


def print_pipeline_result(
    result: object,
    output_folder: str,
) -> None:
    """Print the completed pipeline result."""

    print()
    print("=" * 60)
    print("PRESSSTARTAI RESULT")
    print("=" * 60)
    print(f"Source Video      : {result.source_video_file}")
    print(
        f"Video Duration    : "
        f"{result.video_duration_seconds:.2f}s"
    )
    print(f"Final Highlights  : {result.highlight_count}")
    print(f"Exported Files    : {result.exported_file_count}")
    print(f"Short Packages    : {result.short_package_count}")
    print(
        f"Pipeline Time     : "
        f"{result.total_duration_seconds:.2f}s"
    )
    print(f"Output Folder     : {output_folder}")

    for package in result.short_packages:
        print()
        print("-" * 60)
        print(f"Rank             : {package.rank}")
        print(f"Final Short      : {package.final_video_file}")
        print(f"Captions         : {package.subtitle_file}")
        print(f"Category         : {package.category}")
        print(f"Confidence       : {package.confidence:.4f}")
        print(f"Hook             : {package.metadata.hook}")
        print(f"Title            : {package.metadata.title}")
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



def main() -> None:
    """Run the PressStartAI main menu."""

    arguments = parse_arguments()

    while True:
        choice = display_main_menu()

        if choice == "1":
            selections = select_normal_mode_files()

            if selections is not None:
                run_pipeline(
                    selections=selections,
                    arguments=arguments,
                )

            continue

        if choice == "2":
            selections = select_facecam_mode_files()

            if selections is not None:
                run_pipeline(
                    selections=selections,
                    arguments=arguments,
                )

            continue

        if choice == "3":
            remove_video_background()
            continue

        if choice == "4":
            print("PressStartAI closed.")
            return

        if choice == "5":
            create_ranking_video_from_dialogs()
            continue

        print("Please enter 1, 2, 3, 4, or 5.")


if __name__ == "__main__":
    main()
