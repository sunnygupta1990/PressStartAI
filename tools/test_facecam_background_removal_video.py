# tools/test_facecam_background_removal_video.py

"""Isolated short-video test for local facecam background removal."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2
import numpy as np

from src.services.facecam_background_removal_service import (
    FacecamBackgroundRemovalError,
    RvmOpenVinoMattingService,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Process a short facecam segment with Robust Video Matting "
            "without modifying the PressStartAI pipeline."
        )
    )
    parser.add_argument(
        "video_path",
        type=Path,
        help="Path to the facecam video.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(
            "models/rvm/rvm_mobilenetv3_fp16.onnx"
        ),
        help="Path to the RVM ONNX model.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "output/facecam_background_removal_test/"
            "facecam_matting_preview.mp4"
        ),
        help="Output MP4 path.",
    )
    parser.add_argument(
        "--device",
        default="CPU",
        help="OpenVINO inference device.",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=None,
        help=(
            "Start timestamp in seconds. "
            "Defaults to the middle of the video."
        ),
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Number of seconds to process.",
    )
    parser.add_argument(
        "--downsample-ratio",
        type=float,
        default=0.25,
        help="RVM downsample ratio from 0.05 to 1.0.",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=float,
        default=0.02,
        help="Remove faint alpha values below this threshold.",
    )
    parser.add_argument(
        "--maximum-width",
        type=int,
        default=1280,
        help="Maximum width used during model inference.",
    )

    return parser.parse_args()


def validate_arguments(arguments: argparse.Namespace) -> None:
    """Validate test arguments."""

    if arguments.duration <= 0:
        raise ValueError("Duration must be greater than zero.")

    if arguments.start is not None and arguments.start < 0:
        raise ValueError("Start timestamp cannot be negative.")


def open_video(
    video_path: Path,
) -> tuple[cv2.VideoCapture, float, int, int, float]:
    """Open the source video and return its metadata."""

    normalized_path = video_path.expanduser().resolve()

    if not normalized_path.exists():
        raise FileNotFoundError(
            f"Facecam video was not found: {normalized_path}"
        )

    capture = cv2.VideoCapture(str(normalized_path))

    if not capture.isOpened():
        raise RuntimeError(
            f"Unable to open facecam video: {normalized_path}"
        )

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0:
        capture.release()
        raise RuntimeError(
            "Unable to determine facecam frame rate."
        )

    if width <= 0 or height <= 0:
        capture.release()
        raise RuntimeError(
            "Unable to determine facecam dimensions."
        )

    duration = (
        frame_count / fps
        if frame_count > 0
        else 0.0
    )

    return capture, fps, width, height, duration


def calculate_start_time(
    requested_start: float | None,
    video_duration: float,
    test_duration: float,
) -> float:
    """Choose a safe start timestamp."""

    if requested_start is not None:
        start_time = requested_start
    elif video_duration > 0:
        start_time = max(
            0.0,
            (video_duration - test_duration) / 2.0,
        )
    else:
        start_time = 0.0

    if video_duration > 0:
        maximum_start = max(
            0.0,
            video_duration - min(test_duration, video_duration),
        )
        start_time = min(start_time, maximum_start)

    return start_time


def create_video_writer(
    output_path: Path,
    fps: float,
    source_width: int,
    source_height: int,
) -> cv2.VideoWriter:
    """Create the side-by-side preview writer."""

    normalized_output = output_path.expanduser().resolve()
    normalized_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    preview_width = source_width
    preview_height = source_height

    writer = cv2.VideoWriter(
        str(normalized_output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (preview_width, preview_height),
    )

    if not writer.isOpened():
        raise RuntimeError(
            f"Unable to create preview video: {normalized_output}"
        )

    return writer


def create_checkerboard_background(
    width: int,
    height: int,
    square_size: int = 48,
) -> np.ndarray:
    """Create a checkerboard transparency preview."""

    background = np.empty(
        (height, width, 3),
        dtype=np.uint8,
    )

    light = np.array(
        [215, 215, 215],
        dtype=np.uint8,
    )
    dark = np.array(
        [150, 150, 150],
        dtype=np.uint8,
    )

    for y in range(0, height, square_size):
        for x in range(0, width, square_size):
            use_light = (
                (x // square_size + y // square_size) % 2
                == 0
            )

            background[
                y : y + square_size,
                x : x + square_size,
            ] = light if use_light else dark

    return background


def create_alpha_preview(
    alpha: np.ndarray,
) -> np.ndarray:
    """Convert an alpha mask into a three-channel preview."""

    alpha_8bit = np.clip(
        alpha * 255.0,
        0,
        255,
    ).astype(np.uint8)

    return cv2.cvtColor(
        alpha_8bit,
        cv2.COLOR_GRAY2BGR,
    )


def add_panel_label(
    image: np.ndarray,
    label: str,
) -> np.ndarray:
    """Add a readable label to one preview panel."""

    labeled = image.copy()

    cv2.rectangle(
        labeled,
        (0, 0),
        (260, 52),
        (0, 0, 0),
        thickness=-1,
    )

    cv2.putText(
        labeled,
        label,
        (16, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        thickness=2,
        lineType=cv2.LINE_AA,
    )

    return labeled


def process_video_segment(
    capture: cv2.VideoCapture,
    writer: cv2.VideoWriter,
    service: RvmOpenVinoMattingService,
    start_time: float,
    duration: float,
    fps: float,
    width: int,
    height: int,
) -> tuple[int, float]:
    """Process and save one short facecam segment."""

    capture.set(
        cv2.CAP_PROP_POS_MSEC,
        start_time * 1000.0,
    )

    target_frames = max(
        1,
        round(duration * fps),
    )

    checkerboard = create_checkerboard_background(
        width=width,
        height=height,
    )

    service.reset()

    processed_frames = 0
    started_at = time.perf_counter()

    for frame_number in range(target_frames):
        success, frame = capture.read()

        if not success or frame is None:
            break

        result = service.process_frame(frame)

        preview_frame = result.composite_over(checkerboard)
        writer.write(preview_frame)

        processed_frames += 1

        if (
            frame_number == 0
            or (frame_number + 1) % max(1, round(fps)) == 0
        ):
            elapsed_seconds = time.perf_counter() - started_at

            print(
                f"Processed {frame_number + 1}/{target_frames} "
                f"frames | elapsed: {elapsed_seconds:.1f}s"
            )

    elapsed_seconds = time.perf_counter() - started_at

    return processed_frames, elapsed_seconds


def main() -> None:
    """Run the isolated short-video matting test."""

    arguments = parse_arguments()
    validate_arguments(arguments)

    capture, fps, width, height, video_duration = open_video(
        arguments.video_path
    )

    writer: cv2.VideoWriter | None = None

    try:
        start_time = calculate_start_time(
            requested_start=arguments.start,
            video_duration=video_duration,
            test_duration=arguments.duration,
        )

        writer = create_video_writer(
            output_path=arguments.output,
            fps=fps,
            source_width=width,
            source_height=height,
        )

        service = RvmOpenVinoMattingService(
            model_path=arguments.model,
            device=arguments.device,
            downsample_ratio=arguments.downsample_ratio,
            alpha_threshold=arguments.alpha_threshold,
            maximum_processing_width=arguments.maximum_width,
        )

        print("Starting isolated facecam video test.")
        print(f"Device: {service.device}")
        print(f"Start: {start_time:.3f} seconds")
        print(f"Duration: {arguments.duration:.3f} seconds")
        print(f"Resolution: {width}x{height}")
        print(f"Frame rate: {fps:.3f} FPS")

        processed_frames, elapsed_seconds = process_video_segment(
            capture=capture,
            writer=writer,
            service=service,
            start_time=start_time,
            duration=arguments.duration,
            fps=fps,
            width=width,
            height=height,
        )

    finally:
        capture.release()

        if writer is not None:
            writer.release()

    if processed_frames == 0:
        raise RuntimeError(
            "No facecam frames were processed."
        )

    processing_fps = (
        processed_frames / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    output_path = arguments.output.expanduser().resolve()

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(
            f"Preview video was not created correctly: {output_path}"
        )

    print()
    print("Facecam video test complete.")
    print(f"Processed frames: {processed_frames}")
    print(f"Processing time: {elapsed_seconds:.2f} seconds")
    print(f"Processing speed: {processing_fps:.2f} FPS")
    print(f"Preview: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except (
        FacecamBackgroundRemovalError,
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as error:
        raise SystemExit(
            f"Facecam video test failed: {error}"
        ) from error