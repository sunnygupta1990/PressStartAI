"""Compose cinematic gaming thumbnails from gameplay frames and creator cutouts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
import math

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

from src.thumbnail_generator.services.background_removal_service import CreatorCutout
from src.thumbnail_generator.services.frame_scoring_service import FrameScore


class ThumbnailCompositionError(RuntimeError):
    """Raised when thumbnail composition cannot be completed."""


@dataclass(frozen=True, slots=True)
class ThumbnailVariant:
    """One thumbnail layout and styling variant."""

    caption: str
    descriptive_name: str
    creator_side: str = "right"
    gameplay_zoom: float = 1.06
    creator_scale: float = 0.90
    darken_strength: int = 80


@dataclass(frozen=True, slots=True)
class ComposedThumbnail:
    """One final saved thumbnail."""

    image_path: Path
    caption: str
    frame_score: FrameScore
    variant: ThumbnailVariant
    creator_cutout: CreatorCutout


def compose_thumbnails(
    frame_scores: Sequence[FrameScore],
    creator_cutouts: Sequence[CreatorCutout],
    variants: Sequence[ThumbnailVariant],
    output_directory: Path,
    brand_colors: Sequence[str],
    logo_path: Path | None = None,
    logo_enabled: bool = False,
    width: int = 1280,
    height: int = 720,
    game_title: str | None = None,
    episode_label: str | None = None,
    footer_label: str = "GAMEPLAY",
) -> list[ComposedThumbnail]:
    """Compose multiple cinematic thumbnail candidates."""

    if not frame_scores:
        raise ThumbnailCompositionError("At least one frame score is required.")

    if not creator_cutouts:
        raise ThumbnailCompositionError("At least one creator cutout is required.")

    if not variants:
        raise ThumbnailCompositionError("At least one thumbnail variant is required.")

    normalized_output_directory = output_directory.expanduser().resolve()

    try:
        normalized_output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ThumbnailCompositionError(
            f"Unable to create thumbnail output folder: {error}"
        ) from error

    accent_color = _safe_color(brand_colors[0] if brand_colors else "#1DA1F2")
    secondary_accent = _safe_color(brand_colors[1] if len(brand_colors) > 1 else "#0F172A")
    logo_image = _load_logo(logo_path) if logo_enabled and logo_path else None

    selected_frames = _select_best_frames(frame_scores)
    selected_cutouts = _rank_cutouts(creator_cutouts)

    composed: list[ComposedThumbnail] = []

    for index, variant in enumerate(variants, start=1):
        frame_score = selected_frames[(index - 1) % len(selected_frames)]
        creator_cutout = selected_cutouts[(index - 1) % len(selected_cutouts)]

        try:
            thumbnail_image = _compose_single_thumbnail(
                frame_score=frame_score,
                creator_cutout=creator_cutout,
                variant=variant,
                accent_color=accent_color,
                secondary_accent=secondary_accent,
                logo_image=logo_image,
                width=width,
                height=height,
                game_title=game_title,
                episode_label=episode_label,
                footer_label=footer_label,
            )
        except Exception as error:
            raise ThumbnailCompositionError(
                f"Unable to compose thumbnail '{variant.descriptive_name}': {error}"
            ) from error

        filename = f"thumbnail_{index:02d}_{variant.descriptive_name}.png"
        image_path = normalized_output_directory / filename

        try:
            thumbnail_image.save(image_path, format="PNG", optimize=True)
        except OSError as error:
            raise ThumbnailCompositionError(
                f"Unable to save thumbnail '{image_path.name}': {error}"
            ) from error

        composed.append(
            ComposedThumbnail(
                image_path=image_path,
                caption=variant.caption,
                frame_score=frame_score,
                variant=variant,
                creator_cutout=creator_cutout,
            )
        )

    return composed


def _compose_single_thumbnail(
    frame_score: FrameScore,
    creator_cutout: CreatorCutout,
    variant: ThumbnailVariant,
    accent_color: tuple[int, int, int],
    secondary_accent: tuple[int, int, int],
    logo_image: Image.Image | None,
    width: int,
    height: int,
    game_title: str | None,
    episode_label: str | None,
    footer_label: str,
) -> Image.Image:
    """Compose one cinematic thumbnail."""

    gameplay_image = _load_image(frame_score.image_path)
    creator_image = _load_image(creator_cutout.image_path)

    canvas = _create_gameplay_background(
        gameplay_image=gameplay_image,
        width=width,
        height=height,
        creator_side=variant.creator_side,
        darken_strength=variant.darken_strength,
    )

    focus_region = _build_gameplay_focus_layer(
        gameplay_image=gameplay_image,
        width=width,
        height=height,
        creator_side=variant.creator_side,
        zoom=variant.gameplay_zoom,
    )
    canvas.alpha_composite(focus_region)

    _add_cinematic_lighting(
        canvas=canvas,
        creator_side=variant.creator_side,
        accent_color=accent_color,
        secondary_accent=secondary_accent,
    )

    _paste_creator(
        canvas=canvas,
        creator_image=creator_image,
        creator_side=variant.creator_side,
        creator_scale=variant.creator_scale,
        accent_color=accent_color,
    )

    if game_title:
        _draw_game_title(
            canvas=canvas,
            title_text=game_title,
            creator_side=variant.creator_side,
        )

    _draw_caption_block(
        canvas=canvas,
        caption=variant.caption,
        creator_side=variant.creator_side,
        accent_color=accent_color,
    )

    if episode_label:
        _draw_episode_badge(
            canvas=canvas,
            episode_label=episode_label,
        )

    _draw_footer_label(
        canvas=canvas,
        footer_label=footer_label,
        accent_color=accent_color,
        creator_side=variant.creator_side,
    )

    if logo_image is not None:
        _draw_logo(
            canvas=canvas,
            logo_image=logo_image,
            creator_side=variant.creator_side,
        )

    return canvas.convert("RGB")


def _select_best_frames(
    frame_scores: Sequence[FrameScore],
) -> list[FrameScore]:
    """Prefer the strongest visual frames only."""

    sorted_scores = sorted(
        frame_scores,
        key=lambda score: score.total_score,
        reverse=True,
    )

    strong_scores = [score for score in sorted_scores if score.total_score >= 60.0]

    if not strong_scores:
        strong_scores = sorted_scores[:1]

    return strong_scores[: min(3, len(strong_scores))]


def _rank_cutouts(
    creator_cutouts: Sequence[CreatorCutout],
) -> list[CreatorCutout]:
    """Rank creator cutouts by size and usable portrait shape."""

    def score(cutout: CreatorCutout) -> float:
        area_score = float(cutout.width * cutout.height)
        aspect_ratio = cutout.height / max(cutout.width, 1)
        portrait_bonus = 1.25 if aspect_ratio > 1.1 else 1.0
        return area_score * portrait_bonus

    return sorted(
        creator_cutouts,
        key=score,
        reverse=True,
    )


def _create_gameplay_background(
    gameplay_image: Image.Image,
    width: int,
    height: int,
    creator_side: str,
    darken_strength: int,
) -> Image.Image:
    """Create a cinematic gameplay background with blur and gradients."""

    background = _cover_resize(gameplay_image, width, height)
    background = ImageEnhanceProxy.contrast(background, 1.18)
    background = ImageEnhanceProxy.color(background, 1.15)
    background = background.filter(ImageFilter.GaussianBlur(radius=16))

    vignette = _create_vignette(width, height, strength=160)
    background.alpha_composite(vignette)

    directional_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(directional_overlay)

    if creator_side.lower() == "right":
        draw.rectangle(
            [(0, 0), (int(width * 0.62), height)],
            fill=(0, 0, 0, max(20, min(darken_strength - 15, 110))),
        )
        draw.rectangle(
            [(int(width * 0.62), 0), (width, height)],
            fill=(0, 0, 0, max(30, min(darken_strength + 10, 150))),
        )
    else:
        draw.rectangle(
            [(0, 0), (int(width * 0.38), height)],
            fill=(0, 0, 0, max(30, min(darken_strength + 10, 150))),
        )
        draw.rectangle(
            [(int(width * 0.38), 0), (width, height)],
            fill=(0, 0, 0, max(20, min(darken_strength - 15, 110))),
        )

    directional_overlay = directional_overlay.filter(ImageFilter.GaussianBlur(radius=24))
    background.alpha_composite(directional_overlay)

    return background


def _build_gameplay_focus_layer(
    gameplay_image: Image.Image,
    width: int,
    height: int,
    creator_side: str,
    zoom: float,
) -> Image.Image:
    """Create a sharper gameplay focus panel."""

    focus_crop = _crop_gameplay_focus(
        gameplay_image=gameplay_image,
        width=width,
        height=height,
        creator_side=creator_side,
        zoom=zoom,
    )

    focus_crop = ImageEnhanceProxy.contrast(focus_crop, 1.22)
    focus_crop = ImageEnhanceProxy.sharpness(focus_crop, 1.20)
    focus_crop = ImageEnhanceProxy.color(focus_crop, 1.20)

    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    panel_width = int(width * 0.58)
    panel_height = int(height * 0.72)

    panel = _cover_resize(focus_crop, panel_width, panel_height)
    panel = panel.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))

    mask = Image.new("L", (panel_width, panel_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (panel_width - 1, panel_height - 1)],
        radius=34,
        fill=255,
    )

    framed_panel = Image.new("RGBA", (panel_width + 18, panel_height + 18), (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(framed_panel)
    frame_draw.rounded_rectangle(
        [(0, 0), (panel_width + 17, panel_height + 17)],
        radius=40,
        fill=(0, 0, 0, 120),
    )
    framed_panel.alpha_composite(panel, (9, 9))

    if creator_side.lower() == "right":
        x = 36
    else:
        x = width - panel_width - 54

    y = int(height * 0.12)
    shadow = _make_shadow(mask.resize((panel_width + 18, panel_height + 18)), blur=20, opacity=110)
    layer.alpha_composite(shadow, (x + 10, y + 12))
    layer.alpha_composite(framed_panel, (x, y))

    return layer


def _crop_gameplay_focus(
    gameplay_image: Image.Image,
    width: int,
    height: int,
    creator_side: str,
    zoom: float,
) -> Image.Image:
    """Crop gameplay while preserving dramatic subject area."""

    source_width, source_height = gameplay_image.size
    target_ratio = width / height

    crop_width = int(source_width / max(zoom, 1.0))
    crop_height = int(crop_width / target_ratio)

    if crop_height > source_height:
        crop_height = int(source_height / max(zoom, 1.0))
        crop_width = int(crop_height * target_ratio)

    crop_width = min(crop_width, source_width)
    crop_height = min(crop_height, source_height)

    if creator_side.lower() == "right":
        center_x = int(source_width * 0.36)
    else:
        center_x = int(source_width * 0.64)

    center_y = int(source_height * 0.46)

    left = max(0, min(source_width - crop_width, center_x - crop_width // 2))
    top = max(0, min(source_height - crop_height, center_y - crop_height // 2))
    right = left + crop_width
    bottom = top + crop_height

    return gameplay_image.crop((left, top, right, bottom)).convert("RGBA")


def _add_cinematic_lighting(
    canvas: Image.Image,
    creator_side: str,
    accent_color: tuple[int, int, int],
    secondary_accent: tuple[int, int, int],
) -> None:
    """Add cinematic color glows and screen separation."""

    width, height = canvas.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    blue = (*accent_color, 80)
    red = (255, 50, 35, 70)
    dark = (*secondary_accent, 45)

    if creator_side.lower() == "right":
        draw.ellipse(
            [int(width * 0.56), int(height * 0.02), int(width * 1.02), int(height * 0.78)],
            fill=blue,
        )
        draw.ellipse(
            [int(width * 0.08), int(height * 0.20), int(width * 0.58), int(height * 0.94)],
            fill=red,
        )
    else:
        draw.ellipse(
            [int(width * -0.02), int(height * 0.02), int(width * 0.44), int(height * 0.78)],
            fill=blue,
        )
        draw.ellipse(
            [int(width * 0.42), int(height * 0.20), int(width * 0.92), int(height * 0.94)],
            fill=red,
        )

    draw.rectangle([(0, 0), (width, height)], fill=dark)

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=42))
    canvas.alpha_composite(overlay)


def _paste_creator(
    canvas: Image.Image,
    creator_image: Image.Image,
    creator_side: str,
    creator_scale: float,
    accent_color: tuple[int, int, int],
) -> None:
    """Paste the creator portrait with glow, shadow, and strong presence."""

    width, height = canvas.size
    max_height = int(height * creator_scale)
    max_width = int(width * 0.46)

    prepared = _contain_resize(creator_image, max_width, max_height)
    bbox = prepared.getbbox()

    if bbox:
        prepared = prepared.crop(bbox)

    shadow_mask = prepared.getchannel("A")
    shadow = _make_shadow(shadow_mask, blur=28, opacity=150)
    glow = _make_glow(shadow_mask, accent_color=accent_color)

    base_y = height - prepared.height - 6

    if creator_side.lower() == "right":
        base_x = width - prepared.width - 10
        glow_x = base_x - 10
    else:
        base_x = 10
        glow_x = base_x - 6

    canvas.alpha_composite(shadow, (base_x + 18, base_y + 20))
    canvas.alpha_composite(glow, (glow_x, base_y - 4))
    canvas.alpha_composite(prepared, (base_x, base_y))


def _draw_caption_block(
    canvas: Image.Image,
    caption: str,
    creator_side: str,
    accent_color: tuple[int, int, int],
) -> None:
    """Draw a strong layered caption block."""

    width, height = canvas.size
    draw = ImageDraw.Draw(canvas)

    lines = _caption_lines(caption)
    fill_colors = _caption_colors(line_count=len(lines), accent_color=accent_color)

    if creator_side.lower() == "right":
        left = 34
        right = int(width * 0.60)
    else:
        left = int(width * 0.40)
        right = width - 34

    top = int(height * 0.50)
    max_width = right - left
    max_height = int(height * 0.36)

    font_size = _fit_multiline_font_size(
        draw=draw,
        lines=lines,
        max_width=max_width,
        max_height=max_height,
        initial_size=118,
        minimum_size=44,
    )
    font = _load_bold_font(font_size)
    line_gap = max(8, font_size // 10)

    metrics = [_text_bbox(draw, line, font) for line in lines]
    total_height = sum(metric[3] - metric[1] for metric in metrics) + line_gap * (len(lines) - 1)

    y = max(40, min(height - total_height - 80, top))

    for line, fill_color in zip(lines, fill_colors):
        bbox = _text_bbox(draw, line, font)
        line_height = bbox[3] - bbox[1]

        shadow_offset = max(4, font_size // 18)
        draw.text(
            (left + shadow_offset, y + shadow_offset),
            line,
            font=font,
            fill=(0, 0, 0, 210),
            stroke_width=max(2, font_size // 16),
            stroke_fill=(0, 0, 0, 255),
        )

        draw.text(
            (left, y),
            line,
            font=font,
            fill=fill_color,
            stroke_width=max(2, font_size // 16),
            stroke_fill=(8, 8, 8, 255),
        )

        y += line_height + line_gap


def _draw_game_title(
    canvas: Image.Image,
    title_text: str,
    creator_side: str,
) -> None:
    """Draw a large top game title."""

    width, _ = canvas.size
    draw = ImageDraw.Draw(canvas)

    display_text = title_text.strip().upper()
    font_size = 86

    if len(display_text) > 12:
        font_size = 72

    font = _load_bold_font(font_size)
    bbox = _text_bbox(draw, display_text, font)
    text_width = bbox[2] - bbox[0]

    if creator_side.lower() == "right":
        x = 24
    else:
        x = width - text_width - 24

    y = 18

    draw.text(
        (x + 5, y + 5),
        display_text,
        font=font,
        fill=(0, 0, 0, 220),
        stroke_width=max(2, font_size // 18),
        stroke_fill=(0, 0, 0, 255),
    )
    draw.text(
        (x, y),
        display_text,
        font=font,
        fill=(244, 197, 20, 255),
        stroke_width=max(2, font_size // 18),
        stroke_fill=(20, 20, 20, 255),
    )


def _draw_episode_badge(
    canvas: Image.Image,
    episode_label: str,
) -> None:
    """Draw a top-right episode badge."""

    width, _ = canvas.size
    badge_width = 180
    badge_height = 84

    badge = Image.new("RGBA", (badge_width, badge_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)

    polygon = [
        (8, 14),
        (badge_width - 18, 2),
        (badge_width - 2, badge_height - 18),
        (24, badge_height - 2),
        (0, 42),
    ]
    draw.polygon(polygon, fill=(248, 248, 248, 242))

    font_small = _load_bold_font(32)
    font_big = _load_bold_font(56)

    parts = episode_label.upper().split(maxsplit=1)
    left_text = parts[0]
    right_text = parts[1] if len(parts) > 1 else ""

    draw.text(
        (18, 18),
        left_text,
        font=font_small,
        fill=(18, 18, 18, 255),
    )

    if right_text:
        bbox = _text_bbox(draw, right_text, font_big)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (badge_width - text_width - 16, 8),
            right_text,
            font=font_big,
            fill=(220, 34, 24, 255),
        )

    canvas.alpha_composite(badge, (width - badge_width - 18, 18))


def _draw_footer_label(
    canvas: Image.Image,
    footer_label: str,
    accent_color: tuple[int, int, int],
    creator_side: str,
) -> None:
    """Draw a footer label strip."""

    width, height = canvas.size
    label_text = footer_label.upper().strip()

    if not label_text:
        return

    draw = ImageDraw.Draw(canvas)
    font = _load_bold_font(28)
    bbox = _text_bbox(draw, label_text, font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding_x = 18
    padding_y = 10
    box_width = text_width + padding_x * 2
    box_height = text_height + padding_y * 2

    if creator_side.lower() == "right":
        x = 28
    else:
        x = width - box_width - 28

    y = height - box_height - 24

    pill = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    pill_draw = ImageDraw.Draw(pill)
    pill_draw.rounded_rectangle(
        [(0, 0), (box_width - 1, box_height - 1)],
        radius=18,
        fill=(8, 8, 8, 195),
        outline=(*accent_color, 255),
        width=3,
    )

    canvas.alpha_composite(pill, (x, y))

    draw.text(
        (x + padding_x, y + padding_y - 1),
        label_text,
        font=font,
        fill=(245, 245, 245, 255),
    )


def _draw_logo(
    canvas: Image.Image,
    logo_image: Image.Image,
    creator_side: str,
) -> None:
    """Draw an optional channel logo."""

    width, _ = canvas.size
    max_width = 140
    max_height = 80
    prepared_logo = _contain_resize(logo_image, max_width, max_height)

    if creator_side.lower() == "right":
        x = width - prepared_logo.width - 28
    else:
        x = 28

    y = 108
    canvas.alpha_composite(prepared_logo, (x, y))


def _caption_lines(
    caption: str,
) -> list[str]:
    """Split caption into strong readable lines."""

    words = [word.strip() for word in caption.upper().split() if word.strip()]

    if not words:
        return ["GAMING MOMENT"]

    if len(words) <= 2:
        return [" ".join(words)]

    if len(words) == 3:
        return [" ".join(words[:2]), words[2]]

    if len(words) == 4:
        return [" ".join(words[:2]), " ".join(words[2:])]

    if len(words) == 5:
        return [" ".join(words[:2]), " ".join(words[2:4]), words[4]]

    first_break = math.ceil(len(words) * 0.4)
    second_break = math.ceil(len(words) * 0.75)

    return [
        " ".join(words[:first_break]),
        " ".join(words[first_break:second_break]),
        " ".join(words[second_break:]),
    ]


def _caption_colors(
    line_count: int,
    accent_color: tuple[int, int, int],
) -> list[tuple[int, int, int, int]]:
    """Choose bold caption colors by line order."""

    white = (248, 248, 248, 255)
    yellow = (244, 197, 20, 255)
    red = (220, 34, 24, 255)
    blue = (*accent_color, 255)

    if line_count == 1:
        return [yellow]

    if line_count == 2:
        return [white, red]

    return [white, yellow, red if accent_color != red[:3] else blue]


def _fit_multiline_font_size(
    draw: ImageDraw.ImageDraw,
    lines: Sequence[str],
    max_width: int,
    max_height: int,
    initial_size: int,
    minimum_size: int,
) -> int:
    """Find the largest font size that fits the text box."""

    for font_size in range(initial_size, minimum_size - 1, -2):
        font = _load_bold_font(font_size)
        line_gap = max(8, font_size // 10)

        widths: list[int] = []
        heights: list[int] = []

        for line in lines:
            bbox = _text_bbox(draw, line, font)
            widths.append(bbox[2] - bbox[0])
            heights.append(bbox[3] - bbox[1])

        total_width = max(widths)
        total_height = sum(heights) + line_gap * (len(lines) - 1)

        if total_width <= max_width and total_height <= max_height:
            return font_size

    return minimum_size


def _create_vignette(
    width: int,
    height: int,
    strength: int,
) -> Image.Image:
    """Create a soft dark vignette."""

    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        [(-int(width * 0.10), -int(height * 0.18)), (int(width * 1.10), int(height * 1.18))],
        fill=255,
    )
    mask = ImageOps.invert(mask)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=78))
    vignette.putalpha(mask.point(lambda value: min(strength, value)))
    return vignette


def _make_shadow(
    alpha_mask: Image.Image,
    blur: int,
    opacity: int,
) -> Image.Image:
    """Create a drop shadow from an alpha mask."""

    shadow = Image.new("RGBA", alpha_mask.size, (0, 0, 0, 0))
    shadow.putalpha(alpha_mask.point(lambda value: int(value * (opacity / 255.0))))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur))
    return shadow


def _make_glow(
    alpha_mask: Image.Image,
    accent_color: tuple[int, int, int],
) -> Image.Image:
    """Create an accent-colored outer glow."""

    glow = Image.new(
        "RGBA",
        (alpha_mask.width + 20, alpha_mask.height + 20),
        (0, 0, 0, 0),
    )
    expanded_mask = Image.new("L", glow.size, 0)
    expanded_mask.paste(alpha_mask, (10, 10))
    expanded_mask = expanded_mask.filter(ImageFilter.GaussianBlur(radius=16))

    glow_layer = Image.new("RGBA", glow.size, (*accent_color, 0))
    glow_layer.putalpha(expanded_mask.point(lambda value: min(170, value)))
    return glow_layer


def _load_logo(
    path: Path,
) -> Image.Image | None:
    """Load an optional logo image."""

    if not path.exists():
        return None

    try:
        return _load_image(path)
    except Exception:
        return None


def _load_image(
    path: Path,
) -> Image.Image:
    """Load an image as RGBA."""

    try:
        with Image.open(path) as image:
            return image.convert("RGBA")
    except OSError as error:
        raise ThumbnailCompositionError(f"Unable to load image '{path}': {error}") from error


def _cover_resize(
    image: Image.Image,
    target_width: int,
    target_height: int,
) -> Image.Image:
    """Resize to fully cover the target box."""

    source_width, source_height = image.size
    scale = max(target_width / source_width, target_height / source_height)

    resized_width = max(1, int(source_width * scale))
    resized_height = max(1, int(source_height * scale))

    resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

    left = max(0, (resized_width - target_width) // 2)
    top = max(0, (resized_height - target_height) // 2)

    return resized.crop((left, top, left + target_width, top + target_height)).convert("RGBA")


def _contain_resize(
    image: Image.Image,
    target_width: int,
    target_height: int,
) -> Image.Image:
    """Resize to fit inside the target box."""

    resized = image.copy()
    resized.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
    return resized.convert("RGBA")


def _safe_color(
    value: str,
) -> tuple[int, int, int]:
    """Parse a color string safely."""

    try:
        return ImageColor.getrgb(value)
    except ValueError:
        return (29, 161, 242)


def _text_bbox(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> tuple[int, int, int, int]:
    """Measure one text bounding box."""

    return draw.textbbox((0, 0), text, font=font, stroke_width=max(1, getattr(font, "size", 24) // 18))


def _load_bold_font(
    size: int,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a heavy display font with fallbacks."""

    font_candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
        "C:/Windows/Fonts/trebucbd.ttf",
    ]

    for candidate in font_candidates:
        candidate_path = Path(candidate)

        if not candidate_path.exists():
            continue

        try:
            return ImageFont.truetype(str(candidate_path), size=size)
        except OSError:
            continue

    return ImageFont.load_default()


class ImageEnhanceProxy:
    """Small proxy to avoid importing PIL.ImageEnhance repeatedly."""

    @staticmethod
    def contrast(image: Image.Image, factor: float) -> Image.Image:
        from PIL import ImageEnhance

        return ImageEnhance.Contrast(image).enhance(factor)

    @staticmethod
    def color(image: Image.Image, factor: float) -> Image.Image:
        from PIL import ImageEnhance

        return ImageEnhance.Color(image).enhance(factor)

    @staticmethod
    def sharpness(image: Image.Image, factor: float) -> Image.Image:
        from PIL import ImageEnhance

        return ImageEnhance.Sharpness(image).enhance(factor)