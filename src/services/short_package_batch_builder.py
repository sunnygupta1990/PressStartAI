# src/services/short_package_batch_builder.py

"""Build configured Short packages with bounded parallel rendering."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from src.models.final_highlight import FinalHighlight
from src.models.recording_session import RecordingSession
from src.models.short_metadata import ShortMetadata
from src.models.short_package import ShortPackage
from src.models.shorts_feature_settings import ShortsFeatureSettings
from src.services.facecam_short_renderer import FaceCamShortRenderer
from src.services.short_package_builder import ShortPackageBuilder
from src.services.checkpoint_cache import CheckpointCache
from src.services.resource_manager import ResourceManager


@dataclass(slots=True, frozen=True)
class _PreparedShort:
    """Highlight and optional metadata prepared before rendering."""

    highlight: FinalHighlight
    metadata: ShortMetadata


class ShortPackageBatchBuilder:
    """Build Short packages with sequential AI and parallel rendering."""

    DEFAULT_RENDER_WORKERS = 2

    def __init__(
        self,
        builder: ShortPackageBuilder | None = None,
        facecam_renderer: FaceCamShortRenderer | None = None,
        render_workers: int | None = None,
        feature_settings: ShortsFeatureSettings | None = None,
        checkpoint_cache: CheckpointCache | None = None,
    ) -> None:
        if render_workers is not None and render_workers < 1:
            raise ValueError("render_workers must be at least 1.")

        self.feature_settings = (
            feature_settings
            if feature_settings is not None
            else ShortsFeatureSettings.load()
        )
        self.builder = (
            builder
            if builder is not None
            else ShortPackageBuilder(self.feature_settings)
        )
        self.facecam_renderer = (
            facecam_renderer
            if facecam_renderer is not None
            else FaceCamShortRenderer()
        )
        self.render_workers = render_workers
        self.resource_manager = ResourceManager()
        self._uses_injected_builder = builder is not None
        self.checkpoint_cache = checkpoint_cache

    def build(
        self,
        highlights: list[FinalHighlight],
        output_folder: str,
        recording_session: RecordingSession | None = None,
        layout_type: str | None = None,
    ) -> list[ShortPackage]:
        """Generate configured packages for all approved highlights."""

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
                metadata=self.builder.generate_metadata(highlight),
            )
            for highlight in highlights
        ]

        def checkpoint_stage(item: _PreparedShort) -> str:
            return (
                "Rendered Short "
                f"rank={item.highlight.rank} "
                f"output={output_folder}"
            )

        def load_cached(item: _PreparedShort) -> ShortPackage | None:
            if self.checkpoint_cache is None:
                return None
            cached = self.checkpoint_cache.load(checkpoint_stage(item))
            if cached.hit:
                print(
                    f"[CACHE] Reusing rendered Short rank "
                    f"{item.highlight.rank}"
                )
                return cached.value
            return None

        def save_cached(
            item: _PreparedShort,
            package: ShortPackage,
        ) -> ShortPackage:
            if self.checkpoint_cache is not None:
                self.checkpoint_cache.save(
                    checkpoint_stage(item),
                    package,
                )
                print(
                    f"[CHECKPOINT] Saved rendered Short rank "
                    f"{item.highlight.rank}"
                )
            return package

        def build_with(
            builder: ShortPackageBuilder,
            item: _PreparedShort,
        ) -> ShortPackage:
            cached = load_cached(item)
            if cached is not None:
                return cached
            package = builder.build(
                highlight=item.highlight,
                output_folder=output_folder,
                layout_type=resolved_layout_type,
                recording_session=recording_session,
                metadata=item.metadata,
            )
            return save_cached(item, package)

        resolved_workers = (
            self.render_workers
            if self.render_workers is not None
            else self.resource_manager.workers(
                task_name="Rendering Shorts",
                item_count=len(prepared_shorts),
                memory_per_worker_mb=900,
                maximum_workers=4,
            )
        )

        if (
            resolved_workers == 1
            or len(prepared_shorts) <= 1
            or self._uses_injected_builder
        ):
            return [
                build_with(self.builder, item)
                for item in prepared_shorts
            ]

        def build_one(item: _PreparedShort) -> ShortPackage:
            worker_builder = ShortPackageBuilder(
                feature_settings=self.feature_settings,
            )
            return build_with(worker_builder, item)

        with ThreadPoolExecutor(
            max_workers=resolved_workers,
            thread_name_prefix="short-render",
        ) as executor:
            return list(executor.map(build_one, prepared_shorts))
