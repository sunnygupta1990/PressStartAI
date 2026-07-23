"""Load and validate creator-photo assets for thumbnail generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


class CreatorAssetError(RuntimeError):
    """Raised when creator-photo assets cannot be loaded."""


@dataclass(frozen=True, slots=True)
class CreatorAsset:
    """Validated creator-photo asset."""

    image_path: Path
    width: int
    height: int
    image_format: str
    has_transparency: bool

    @property
    def resolution_text(self) -> str:
        """Return the image resolution."""

        return f"{self.width}x{self.height}"


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def load_creator_assets(
    assets_directory: Path,
) -> list[CreatorAsset]:
    """Load all valid creator-photo assets from one directory."""

    normalized_directory = assets_directory.expanduser().resolve()

    if not normalized_directory.exists():
        raise CreatorAssetError(
            f"Creator-photo folder was not found: "
            f"{normalized_directory}"
        )

    if not normalized_directory.is_dir():
        raise CreatorAssetError(
            f"Creator-photo path is not a folder: "
            f"{normalized_directory}"
        )

    image_paths = sorted(
        path
        for path in normalized_directory.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not image_paths:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise CreatorAssetError(
            f"No creator photos were found in "
            f"'{normalized_directory}'. "
            f"Supported formats: {supported}"
        )

    valid_assets: list[CreatorAsset] = []
    invalid_files: list[str] = []

    for image_path in image_paths:
        try:
            valid_assets.append(
                _load_single_asset(image_path)
            )
        except CreatorAssetError:
            invalid_files.append(image_path.name)

    if not valid_assets:
        invalid_text = ", ".join(invalid_files)
        raise CreatorAssetError(
            "No valid creator photos could be loaded. "
            f"Invalid files: {invalid_text}"
        )

    return valid_assets


def _load_single_asset(image_path: Path) -> CreatorAsset:
    """Validate and describe one creator-photo asset."""

    try:
        with Image.open(image_path) as image:
            image.verify()

        with Image.open(image_path) as image:
            width, height = image.size
            image_format = image.format or "UNKNOWN"
            has_transparency = _has_transparency(image)

    except UnidentifiedImageError as error:
        raise CreatorAssetError(
            f"Unsupported or damaged image: {image_path}"
        ) from error
    except OSError as error:
        raise CreatorAssetError(
            f"Unable to read creator photo "
            f"'{image_path}': {error}"
        ) from error

    if width <= 0 or height <= 0:
        raise CreatorAssetError(
            f"Creator photo has invalid dimensions: {image_path}"
        )

    return CreatorAsset(
        image_path=image_path,
        width=width,
        height=height,
        image_format=image_format.upper(),
        has_transparency=has_transparency,
    )


def _has_transparency(image: Image.Image) -> bool:
    """Check whether an image contains transparency."""

    if image.mode in {"RGBA", "LA"}:
        alpha_channel = image.getchannel("A")
        minimum_alpha, _ = alpha_channel.getextrema()
        return minimum_alpha < 255

    if image.mode == "P":
        return "transparency" in image.info

    return False