"""Video input model for the thumbnail-generator workflow."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class VideoMode(str, Enum):
    """Supported thumbnail-generation video modes."""

    FULL_GAMEPLAY = "full_gameplay"
    EXISTING_HIGHLIGHT = "existing_highlight"


class VideoRequestError(ValueError):
    """Raised when video request data is invalid."""


@dataclass(frozen=True, slots=True)
class VideoRequest:
    """Validated input for one thumbnail-generation run."""

    profile_key: str
    channel_name: str
    video_mode: VideoMode
    video_path: Path
    game_name: str
    video_type: str
    episode_topic: str

    SUPPORTED_EXTENSIONS = {
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".webm",
        ".m4v",
    }

    def __post_init__(self) -> None:
        """Validate the video request after creation."""

        normalized_path = self.video_path.expanduser().resolve()
        object.__setattr__(self, "video_path", normalized_path)

        self._validate_required_text("profile_key", self.profile_key)
        self._validate_required_text("channel_name", self.channel_name)
        self._validate_required_text("game_name", self.game_name)
        self._validate_required_text("video_type", self.video_type)
        self._validate_required_text("episode_topic", self.episode_topic)

        if not normalized_path.exists():
            raise VideoRequestError(
                f"Video file was not found: {normalized_path}"
            )

        if not normalized_path.is_file():
            raise VideoRequestError(
                f"Video path is not a file: {normalized_path}"
            )

        extension = normalized_path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS))
            raise VideoRequestError(
                f"Unsupported video format '{extension}'. "
                f"Supported formats: {supported}"
            )

    @staticmethod
    def _validate_required_text(field_name: str, value: str) -> None:
        """Validate one required text field."""

        if not isinstance(value, str) or not value.strip():
            readable_name = field_name.replace("_", " ")
            raise VideoRequestError(
                f"{readable_name.capitalize()} is required."
            )