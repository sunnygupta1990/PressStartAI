"""Remove creator-photo backgrounds locally with rembg."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rembg import new_session, remove

from src.thumbnail_generator.services.creator_asset_service import (
    CreatorAsset,
)


class BackgroundRemovalError(RuntimeError):
    """Raised when creator-photo background removal fails."""


@dataclass(frozen=True, slots=True)
class CreatorCutout:
    """Transparent creator image produced from one source asset."""

    source_asset: CreatorAsset
    image_path: Path
    width: int
    height: int

    @property
    def resolution_text(self) -> str:
        """Return the cutout resolution."""

        return f"{self.width}x{self.height}"


def remove_creator_backgrounds(
    assets: list[CreatorAsset],
    output_directory: Path,
    model_name: str = "u2net_human_seg",
) -> list[CreatorCutout]:
    """Remove backgrounds from all creator-photo assets."""

    if not assets:
        raise BackgroundRemovalError(
            "At least one creator-photo asset is required."
        )

    normalized_output_directory = (
        output_directory.expanduser().resolve()
    )

    try:
        normalized_output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as error:
        raise BackgroundRemovalError(
            f"Unable to create cutout output folder "
            f"'{normalized_output_directory}': {error}"
        ) from error

    try:
        session = new_session(model_name)
    except Exception as error:
        raise BackgroundRemovalError(
            f"Unable to load rembg model '{model_name}': {error}"
        ) from error

    cutouts: list[CreatorCutout] = []

    for index, asset in enumerate(assets, start=1):
        output_path = normalized_output_directory / _build_filename(
            asset,
            index,
        )

        cutouts.append(
            _remove_single_background(
                asset=asset,
                output_path=output_path,
                session=session,
            )
        )

    return cutouts


def _remove_single_background(
    asset: CreatorAsset,
    output_path: Path,
    session: object,
) -> CreatorCutout:
    """Remove the background from one creator photo."""

    try:
        with Image.open(asset.image_path) as source_image:
            source_rgba = source_image.convert("RGBA")
            result = remove(
                source_rgba,
                session=session,
            )
    except UnidentifiedImageError as error:
        raise BackgroundRemovalError(
            f"Unsupported or damaged image: {asset.image_path}"
        ) from error
    except OSError as error:
        raise BackgroundRemovalError(
            f"Unable to read creator photo "
            f"'{asset.image_path}': {error}"
        ) from error
    except Exception as error:
        raise BackgroundRemovalError(
            f"Background removal failed for "
            f"'{asset.image_path.name}': {error}"
        ) from error

    if not isinstance(result, Image.Image):
        raise BackgroundRemovalError(
            f"rembg returned an unexpected result for "
            f"'{asset.image_path.name}'."
        )

    result_rgba = result.convert("RGBA")

    try:
        result_rgba.save(
            output_path,
            format="PNG",
            optimize=True,
        )
    except OSError as error:
        raise BackgroundRemovalError(
            f"Unable to save creator cutout "
            f"'{output_path}': {error}"
        ) from error

    if not output_path.exists() or output_path.stat().st_size == 0:
        output_path.unlink(missing_ok=True)
        raise BackgroundRemovalError(
            f"Creator cutout was not created correctly: {output_path}"
        )

    width, height = result_rgba.size

    return CreatorCutout(
        source_asset=asset,
        image_path=output_path,
        width=width,
        height=height,
    )


def _build_filename(
    asset: CreatorAsset,
    sequence: int,
) -> str:
    """Build a descriptive transparent PNG filename."""

    safe_stem = "".join(
        character.lower()
        if character.isalnum()
        else "_"
        for character in asset.image_path.stem
    )

    safe_stem = "_".join(
        part
        for part in safe_stem.split("_")
        if part
    )

    if not safe_stem:
        safe_stem = "creator"

    return (
        f"creator_cutout_{sequence:02d}_"
        f"{safe_stem}.png"
    )