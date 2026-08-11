# src/services/short_package_builder.py

"""Build one configurable ready-to-publish Short package."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.models.final_highlight import FinalHighlight
from src.models.recording_session import RecordingSession
from src.models.short_metadata import ShortMetadata
from src.models.short_package import ShortPackage
from src.models.shorts_feature_settings import ShortsFeatureSettings
from src.services.caption_renderer import CaptionRenderer
from src.services.caption_segment_builder import CaptionSegmentBuilder
from src.services.facecam_short_renderer import FaceCamShortRenderer
from src.services.short_metadata_generator import ShortMetadataGenerator
from src.services.short_renderer import ShortRenderer
from src.services.srt_writer import SRTWriter


class ShortPackageBuilder:
    """Build one Short while honoring shared feature settings."""

    def __init__(
        self,
        feature_settings: ShortsFeatureSettings | None = None,
    ) -> None:
        self.feature_settings = (
            feature_settings
            if feature_settings is not None
            else ShortsFeatureSettings.load()
        )
        self.short_renderer = ShortRenderer()
        self.facecam_renderer = FaceCamShortRenderer()
        self.caption_builder = CaptionSegmentBuilder()
        self.srt_writer = SRTWriter()
        self.caption_renderer = CaptionRenderer()
        self.metadata_generator = ShortMetadataGenerator()

    def generate_metadata(
        self,
        highlight: FinalHighlight,
    ) -> ShortMetadata:
        """Generate AI metadata or a zero-cost placeholder."""

        if self.feature_settings.metadata_enabled:
            return self.metadata_generator.generate(highlight)

        return ShortMetadata(
            rank=highlight.rank,
            hook="",
            title="",
            description="",
            hashtags=[],
            thumbnail_prompt="",
        )

    def build(
        self,
        highlight: FinalHighlight,
        output_folder: str,
        layout_type: str,
        recording_session: RecordingSession | None = None,
        metadata: ShortMetadata | None = None,
    ) -> ShortPackage:
        """Build one configured Short package."""

        output_path = Path(output_folder)
        short_folder = output_path / f"short_{highlight.rank:03d}"
        short_folder.mkdir(parents=True, exist_ok=True)

        subtitle_file = ""
        captions = []

        if self.feature_settings.captions_enabled:
            captions = self.caption_builder.build(highlight)
            subtitle_file = self.srt_writer.write(
                captions=captions,
                output_file=str(short_folder / "captions.srt"),
            )

        final_video_path = short_folder / "final_short.mp4"

        if layout_type in {"facecam", "face_top"}:
            if recording_session is None:
                raise ValueError(
                    "Recording session is required for Facecam Mode."
                )

            rendered_short = self.facecam_renderer.render(
                highlight=highlight,
                recording_session=recording_session,
                output_folder=str(short_folder),
                subtitle_file=subtitle_file or None,
                output_file_name=final_video_path.name,
            )
            final_video_file = rendered_short.file_path
        else:
            rendered_short = self.short_renderer.render(
                highlight=highlight,
                output_folder=str(short_folder),
            )

            if captions and subtitle_file:
                final_video_file = self.caption_renderer.render(
                    video_file=rendered_short.file_path,
                    subtitle_file=subtitle_file,
                    output_file=str(final_video_path),
                )
            else:
                shutil.copy2(
                    rendered_short.file_path,
                    final_video_path,
                )
                final_video_file = str(final_video_path)

        resolved_metadata = (
            metadata
            if metadata is not None
            else self.generate_metadata(highlight)
        )

        return ShortPackage(
            rendered_short=rendered_short,
            final_video_file=final_video_file,
            subtitle_file=subtitle_file,
            metadata=resolved_metadata,
        )
