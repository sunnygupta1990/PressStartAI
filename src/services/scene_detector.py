from pathlib import Path

from scenedetect import ContentDetector, detect

from src.models.scene import Scene


class SceneDetector:
    """Detect and filter visual scene changes in video files."""

    def __init__(
        self,
        threshold: float = 27.0,
        minimum_scene_length_frames: int = 15,
        minimum_scene_duration_seconds: float = 2.0,
    ) -> None:
        self.threshold = threshold
        self.minimum_scene_length_frames = minimum_scene_length_frames
        self.minimum_scene_duration_seconds = minimum_scene_duration_seconds

    def detect(self, video_file: str) -> list[Scene]:
        video_path = Path(video_file)

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file does not exist: {video_path}"
            )

        detected_scenes = detect(
            str(video_path),
            ContentDetector(
                threshold=self.threshold,
                min_scene_len=self.minimum_scene_length_frames,
            ),
            show_progress=False,
        )

        raw_scenes = [
            Scene(
                start_seconds=start_time.get_seconds(),
                end_seconds=end_time.get_seconds(),
            )
            for start_time, end_time in detected_scenes
        ]

        return self._merge_short_scenes(raw_scenes)

    def _merge_short_scenes(
        self,
        scenes: list[Scene],
    ) -> list[Scene]:
        if not scenes:
            return []

        merged: list[Scene] = []

        current_start = scenes[0].start_seconds
        current_end = scenes[0].end_seconds

        for scene in scenes[1:]:
            current_duration = current_end - current_start

            if current_duration < self.minimum_scene_duration_seconds:
                current_end = scene.end_seconds
                continue

            merged.append(
                Scene(
                    start_seconds=current_start,
                    end_seconds=current_end,
                )
            )

            current_start = scene.start_seconds
            current_end = scene.end_seconds

        merged.append(
            Scene(
                start_seconds=current_start,
                end_seconds=current_end,
            )
        )

        return merged