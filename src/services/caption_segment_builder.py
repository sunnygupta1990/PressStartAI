from src.models.caption_segment import CaptionSegment
from src.models.final_highlight import FinalHighlight


class CaptionSegmentBuilder:
    """Build timed caption segments from an approved highlight transcript."""

    def __init__(
        self,
        maximum_words_per_caption: int = 4,
    ) -> None:
        if maximum_words_per_caption <= 0:
            raise ValueError(
                "maximum_words_per_caption must be greater than zero."
            )

        self.maximum_words_per_caption = (
            maximum_words_per_caption
        )

    def build(
        self,
        highlight: FinalHighlight,
    ) -> list[CaptionSegment]:
        transcript = (
            highlight.transcript_text.strip()
        )

        if not transcript:
            return []

        words = transcript.split()

        caption_texts = [
            " ".join(
                words[
                    index:
                    index + self.maximum_words_per_caption
                ]
            )
            for index in range(
                0,
                len(words),
                self.maximum_words_per_caption,
            )
        ]

        caption_count = len(
            caption_texts
        )

        if caption_count == 0:
            return []

        caption_duration = (
            highlight.duration_seconds
            / caption_count
        )

        captions: list[CaptionSegment] = []

        for index, caption_text in enumerate(
            caption_texts
        ):
            start_seconds = (
                index * caption_duration
            )

            if index == caption_count - 1:
                end_seconds = (
                    highlight.duration_seconds
                )
            else:
                end_seconds = (
                    start_seconds
                    + caption_duration
                )

            captions.append(
                CaptionSegment(
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    text=caption_text,
                )
            )

        return captions