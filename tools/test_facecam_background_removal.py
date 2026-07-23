# tools/test_facecam_background_removal.py

"""Isolated one-frame test for local facecam background removal."""

from __future__ import annotations

import argparse
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
            "Test Robust Video Matting on one frame "
            "without touching the PressStartAI pipeline."
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
        "--output-dir",
        type=Path,
        default=Path(
            "output/facecam_background_removal_test"
        ),
        help="Folder for test outputs.",
    )
    parser.add_argument(
        "--device",
        default="CPU",
        help="OpenVINO device, for example CPU or GPU.",
    )
    parser.add_argument(
        "--timestamp",
        type=float,
        default=None,
        help=(
            "Frame timestamp in seconds. "
            "Defaults to the middle of the video."
        ),
    )
    parser.add_argument(
        "--downsample-ratio",
        type=float,
        default=0.25,
        help="RVM processing ratio between 0.05 and 1.0.",
    )
    parser.add_argument(
        "--maximum-width",
        type=int,
        default=1280,
        help="Maximum processing width.",
    )

    return parser.parse_args()


def read_test_frame(
    video_path: Path,
    timestamp_seconds: float | None,
) -> tuple[np.ndarray, float]:
    """Read one frame from a facecam video."""

    normalized_path = video_path.expanduser().resolve()

    if not normalized_path.exists():
        raise FileNotFoundError(
            f"Video was not found: {normalized_path}"
        )

    capture = cv2.VideoCapture(str(normalized_path))

    if not capture.isOpened():
        raise RuntimeError(
            f"Unable to open video: {normalized_path}"
        )

    try:
        frame_count = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )
        frame_rate = float(
            capture.get(cv2.CAP_PROP_FPS)
        )

        if frame_rate <= 0:
            raise RuntimeError(
                "Video frame rate could not be detected."
            )

        duration_seconds = (
            frame_count / frame_rate
            if frame_count > 0
            else 0.0
        )

        selected_timestamp = timestamp_seconds

        if selected_timestamp is None:
            selected_timestamp = max(
                0.0,
                duration_seconds / 2.0,
            )

        if duration_seconds > 0:
            selected_timestamp = min(
                selected_timestamp,
                max(0.0, duration_seconds - 0.1),
            )

        capture.set(
            cv2.CAP_PROP_POS_MSEC,
            selected_timestamp * 1000.0,
        )

        success, frame = capture.read()

        if not success or frame is None:
            raise RuntimeError(
                "Unable to read the selected facecam frame."
            )

        return frame, selected_timestamp

    finally:
        capture.release()


def create_alpha_preview(
    alpha: np.ndarray,
) -> np.ndarray:
    """Convert a float alpha mask into a visible grayscale image."""

    return np.clip(
        alpha * 255.0,
        0,
        255,
    ).astype(np.uint8)


def create_rgba_cutout(
    foreground_bgr: np.ndarray,
    alpha: np.ndarray,
) -> np.ndarray:
    """Create a BGRA cutout preview."""

    alpha_channel = create_alpha_preview(alpha)

    return cv2.cvtColor(
        foreground_bgr,
        cv2.COLOR_BGR2BGRA,
    ).astype(np.uint8) * np.array(
        [1, 1, 1, 0],
        dtype=np.uint8,
    ) + np.dstack(
        [
            np.zeros_like(alpha_channel),
            np.zeros_like(alpha_channel),
            np.zeros_like(alpha_channel),
            alpha_channel,
        ]
    )


def create_checkerboard_background(
    width: int,
    height: int,
    square_size: int = 48,
) -> np.ndarray:
    """Create a checkerboard background for transparency preview."""

    background = np.zeros(
        (height, width, 3),
        dtype=np.uint8,
    )

    light = np.array(
        [210, 210, 210],
        dtype=np.uint8,
    )
    dark = np.array(
        [155, 155, 155],
        dtype=np.uint8,
    )

    for y in range(0, height, square_size):
        for x in range(0, width, square_size):
            color = (
                light
                if (
                    x // square_size
                    + y // square_size
                )
                % 2
                == 0
                else dark
            )

            background[
                y : y + square_size,
                x : x + square_size,
            ] = color

    return background


def save_image(
    path: Path,
    image: np.ndarray,
) -> None:
    """Save one image and validate the result."""

    if not cv2.imwrite(str(path), image):
        raise RuntimeError(
            f"Unable to save image: {path}"
        )


def main() -> None:
    """Run the isolated one-frame matting test."""

    arguments = parse_arguments()

    output_directory = (
        arguments.output_dir.expanduser().resolve()
    )
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame, timestamp_seconds = read_test_frame(
        video_path=arguments.video_path,
        timestamp_seconds=arguments.timestamp,
    )

    service = RvmOpenVinoMattingService(
        model_path=arguments.model,
        device=arguments.device,
        downsample_ratio=arguments.downsample_ratio,
        maximum_processing_width=arguments.maximum_width,
    )

    service.reset()
    result = service.process_frame(frame)

    height, width = frame.shape[:2]

    checkerboard = create_checkerboard_background(
        width=width,
        height=height,
    )

    composite = result.composite_over(
        checkerboard
    )
    alpha_preview = create_alpha_preview(
        result.alpha
    )
    rgba_cutout = create_rgba_cutout(
        foreground_bgr=result.foreground_bgr,
        alpha=result.alpha,
    )

    original_path = (
        output_directory / "original_frame.jpg"
    )
    alpha_path = (
        output_directory / "alpha_mask.png"
    )
    cutout_path = (
        output_directory / "transparent_cutout.png"
    )
    composite_path = (
        output_directory / "checkerboard_composite.jpg"
    )

    save_image(original_path, frame)
    save_image(alpha_path, alpha_preview)
    save_image(cutout_path, rgba_cutout)
    save_image(composite_path, composite)

    print("Facecam background-removal test complete.")
    print(f"Timestamp: {timestamp_seconds:.3f} seconds")
    print(f"Original: {original_path}")
    print(f"Alpha mask: {alpha_path}")
    print(f"Transparent cutout: {cutout_path}")
    print(f"Composite preview: {composite_path}")


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
            f"Facecam background-removal test failed: {error}"
        ) from error