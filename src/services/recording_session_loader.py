from pathlib import Path

from src.models.recording_session import RecordingSession


class RecordingSessionLoader:
    """Validate and load explicitly selected recording files."""

    SUPPORTED_EXTENSION = ".mp4"

    def load(
        self,
        video_file: str,
        layout_type: str,
        gameplay_video: str | None = None,
        facecam_video: str | None = None,
    ) -> RecordingSession:
        recording_path = self._validate_video(
            video_file,
            "Normal recording",
        )

        if layout_type == "portrait":
            return RecordingSession(
                recording_video=str(recording_path),
            )

        if layout_type != "face_top":
            raise ValueError(
                f"Unsupported layout type: {layout_type}"
            )

        if not gameplay_video:
            raise ValueError(
                "Gameplay recording is required in Facecam Mode."
            )

        if not facecam_video:
            raise ValueError(
                "Facecam recording is required in Facecam Mode."
            )

        gameplay_path = self._validate_video(
            gameplay_video,
            "Gameplay recording",
        )
        facecam_path = self._validate_video(
            facecam_video,
            "Facecam recording",
        )

        selected_paths = {
            recording_path.resolve(),
            gameplay_path.resolve(),
            facecam_path.resolve(),
        }

        if len(selected_paths) != 3:
            raise ValueError(
                "Normal, gameplay, and facecam recordings "
                "must be three different files."
            )

        return RecordingSession(
            recording_video=str(recording_path),
            gameplay_video=str(gameplay_path),
            facecam_video=str(facecam_path),
        )

    def _validate_video(
        self,
        video_file: str,
        display_name: str,
    ) -> Path:
        video_path = Path(video_file).expanduser()

        if not video_path.is_file():
            raise FileNotFoundError(
                f"{display_name} not found: {video_path}"
            )

        if video_path.suffix.lower() != self.SUPPORTED_EXTENSION:
            raise ValueError(
                f"{display_name} must be an MP4 file: {video_path}"
            )

        return video_path