from src.models.final_highlight import FinalHighlight
from src.models.rendered_short import RenderedShort
from src.services.short_renderer import ShortRenderer


class ShortBatchRenderer:
    """Render all final approved highlights as vertical Shorts."""

    def __init__(
        self,
        renderer: ShortRenderer | None = None,
    ) -> None:
        self.renderer = (
            renderer
            if renderer is not None
            else ShortRenderer()
        )

    def render(
        self,
        highlights: list[FinalHighlight],
        output_folder: str,
    ) -> list[RenderedShort]:
        rendered_shorts: list[RenderedShort] = []

        for highlight in highlights:
            rendered_shorts.append(
                self.renderer.render(
                    highlight=highlight,
                    output_folder=output_folder,
                )
            )

        return rendered_shorts