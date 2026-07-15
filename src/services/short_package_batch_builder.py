from src.models.final_highlight import FinalHighlight
from src.models.short_package import ShortPackage
from src.services.short_package_builder import ShortPackageBuilder


class ShortPackageBatchBuilder:
    """Build complete Short packages for all approved highlights."""

    def __init__(
        self,
        builder: ShortPackageBuilder | None = None,
    ) -> None:
        self.builder = (
            builder
            if builder is not None
            else ShortPackageBuilder()
        )

    def build(
        self,
        highlights: list[FinalHighlight],
        output_folder: str,
    ) -> list[ShortPackage]:
        packages: list[ShortPackage] = []

        for highlight in highlights:
            package = self.builder.build(
                highlight=highlight,
                output_folder=output_folder,
            )

            packages.append(
                package
            )

        return packages