from pathlib import Path

from src.models.final_highlight import FinalHighlight
from src.models.short_package import ShortPackage
from src.services.caption_renderer import CaptionRenderer
from src.services.caption_segment_builder import CaptionSegmentBuilder
from src.services.short_metadata_generator import ShortMetadataGenerator
from src.services.short_renderer import ShortRenderer
from src.services.srt_writer import SRTWriter


class ShortPackageBuilder:
    """Build a complete ready-to-publish package for one Short."""

    def __init__(self) -> None:
        self.short_renderer = ShortRenderer()
        self.caption_builder = CaptionSegmentBuilder()
        self.srt_writer = SRTWriter()
        self.caption_renderer = CaptionRenderer()
        self.metadata_generator = ShortMetadataGenerator()

    def build(
        self,
        highlight: FinalHighlight,
        output_folder: str,
    ) -> ShortPackage:
        output_path = Path(
            output_folder
        )

        short_folder = output_path / (
            f"short_{highlight.rank:03d}"
        )

        short_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        rendered_short = self.short_renderer.render(
            highlight=highlight,
            output_folder=str(short_folder),
        )

        captions = self.caption_builder.build(
            highlight
        )

        subtitle_file = self.srt_writer.write(
            captions=captions,
            output_file=str(
                short_folder / "captions.srt"
            ),
        )

        final_video_file = self.caption_renderer.render(
            video_file=rendered_short.file_path,
            subtitle_file=subtitle_file,
            output_file=str(
                short_folder / "final_short.mp4"
            ),
        )

        metadata = self.metadata_generator.generate(
            highlight
        )

        return ShortPackage(
            rendered_short=rendered_short,
            final_video_file=final_video_file,
            subtitle_file=subtitle_file,
            metadata=metadata,
        )