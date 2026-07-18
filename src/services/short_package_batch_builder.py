# src/services/short_package_batch_builder.py

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from src.models.final_highlight import FinalHighlight
from src.models.recording_session import RecordingSession
from src.models.short_metadata import ShortMetadata
from src.models.short_package import ShortPackage
from src.services.facecam_short_renderer import FaceCamShortRenderer
from src.services.short_package_builder import ShortPackageBuilder


@dataclass(slots=True, frozen=True)
class _PreparedShort:
    """Highlight and metadata prepared before parallel rendering."""

    highlight: FinalHighlight
    metadata: ShortMetadata


class ShortPackageBatchBuilder:
    """Build Short packages with sequential AI and parallel rendering."""

    DEFAULT_RENDER_WORKERS = 2

    def __init__(
        self,
        builder: ShortPackageBuilder | None = None,
        facecam_renderer: FaceCamShortRenderer | None = None,
        render_workers: int = DEFAULT_RENDER_WORKERS,
    ) -> None:
        if render_workers < 1:
            raise ValueError(
                "render_workers must be at least 1."
            )

        self.builder = (
            builder
            if builder is not None
            else ShortPackageBuilder()
        )
        self.facecam_renderer = (
            facecam_renderer
            if facecam_renderer is not None
            else FaceCamShortRenderer()
        )
        self.render_workers = render_workers
        self._uses_injected_builder = builder is not None

    def build(
        self,
        highlights: list[FinalHighlight],
        output_folder: str,
        recording_session: RecordingSession | None = None,
        layout_type: str | None = None,
    ) -> list[ShortPackage]:
        """Generate metadata sequentially, then render in parallel."""

        resolved_layout_type = layout_type or "portrait"

        if recording_session is not None:
            if recording_session.has_facecam_layout:
                self.facecam_renderer.validate(recording_session)
                resolved_layout_type = "face_top"
            else:
                resolved_layout_type = "portrait"

        prepared_shorts = [
            _PreparedShort(
                highlight=highlight,
                metadata=self.builder.generate_metadata(
                    highlight
                ),
            )
            for highlight in highlights
        ]

        if (
            self.render_workers == 1
            or len(prepared_shorts) <= 1
            or self._uses_injected_builder
        ):
            return [
                self.builder.build(
                    highlight=item.highlight,
                    output_folder=output_folder,
                    layout_type=resolved_layout_type,
                    recording_session=recording_session,
                    metadata=item.metadata,
                )
                for item in prepared_shorts
            ]

        def build_one(
            item: _PreparedShort,
        ) -> ShortPackage:
            worker_builder = ShortPackageBuilder()

            return worker_builder.build(
                highlight=item.highlight,
                output_folder=output_folder,
                layout_type=resolved_layout_type,
                recording_session=recording_session,
                metadata=item.metadata,
            )

        with ThreadPoolExecutor(
            max_workers=self.render_workers,
            thread_name_prefix="short-render",
        ) as executor:
            return list(
                executor.map(
                    build_one,
                    prepared_shorts,
                )
            )
