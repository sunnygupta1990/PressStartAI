from pathlib import Path

import cv2
import numpy as np

from src.models.motion_features import MotionFeatures
from src.models.scene import Scene


class MotionAnalyzer:
    """Measure visual motion inside detected video scenes."""

    def __init__(
        self,
        sample_interval_frames: int = 5,
    ) -> None:
        self.sample_interval_frames = sample_interval_frames

    def analyze(
        self,
        video_file: str,
        scenes: list[Scene],
    ) -> list[MotionFeatures]:
        video_path = Path(video_file)

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file does not exist: {video_path}"
            )

        capture = cv2.VideoCapture(str(video_path))

        if not capture.isOpened():
            raise RuntimeError(
                f"Unable to open video: {video_path}"
            )

        fps = capture.get(cv2.CAP_PROP_FPS)

        if fps <= 0:
            capture.release()
            raise RuntimeError("Unable to determine video FPS.")

        results: list[MotionFeatures] = []

        try:
            for scene in scenes:
                results.append(
                    self._analyze_scene(
                        capture=capture,
                        fps=fps,
                        scene=scene,
                    )
                )
        finally:
            capture.release()

        return results

    def _analyze_scene(
        self,
        capture: cv2.VideoCapture,
        fps: float,
        scene: Scene,
    ) -> MotionFeatures:
        start_frame = int(scene.start_seconds * fps)
        end_frame = int(scene.end_seconds * fps)

        capture.set(
            cv2.CAP_PROP_POS_FRAMES,
            start_frame,
        )

        previous_gray: np.ndarray | None = None
        motion_scores: list[float] = []

        frame_number = start_frame

        while frame_number < end_frame:
            success, frame = capture.read()

            if not success:
                break

            if (
                frame_number - start_frame
            ) % self.sample_interval_frames != 0:
                frame_number += 1
                continue

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY,
            )

            gray = cv2.GaussianBlur(
                gray,
                (5, 5),
                0,
            )

            if previous_gray is not None:
                difference = cv2.absdiff(
                    previous_gray,
                    gray,
                )

                motion_score = float(
                    np.mean(difference)
                )

                motion_scores.append(motion_score)

            previous_gray = gray
            frame_number += 1

        if not motion_scores:
            return MotionFeatures(
                scene_start_seconds=scene.start_seconds,
                scene_end_seconds=scene.end_seconds,
                average_motion_score=0.0,
                maximum_motion_score=0.0,
            )

        return MotionFeatures(
            scene_start_seconds=scene.start_seconds,
            scene_end_seconds=scene.end_seconds,
            average_motion_score=float(
                np.mean(motion_scores)
            ),
            maximum_motion_score=float(
                np.max(motion_scores)
            ),
        )