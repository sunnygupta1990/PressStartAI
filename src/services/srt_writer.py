from pathlib import Path

from src.models.caption_segment import CaptionSegment


class SRTWriter:
    """Write timed caption segments to an SRT subtitle file."""

    def write(
        self,
        captions: list[CaptionSegment],
        output_file: str,
    ) -> str:
        output_path = Path(
            output_file
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        blocks: list[str] = []

        for index, caption in enumerate(
            captions,
            start=1,
        ):
            start_time = self._format_timestamp(
                caption.start_seconds
            )

            end_time = self._format_timestamp(
                caption.end_seconds
            )

            blocks.append(
                "\n".join(
                    [
                        str(index),
                        f"{start_time} --> {end_time}",
                        caption.text,
                    ]
                )
            )

        content = "\n\n".join(
            blocks
        )

        if content:
            content += "\n"

        output_path.write_text(
            content,
            encoding="utf-8",
        )

        return str(
            output_path
        )

    @staticmethod
    def _format_timestamp(
        seconds: float,
    ) -> str:
        total_milliseconds = max(
            0,
            round(seconds * 1000),
        )

        hours = (
            total_milliseconds
            // 3_600_000
        )

        remaining_milliseconds = (
            total_milliseconds
            % 3_600_000
        )

        minutes = (
            remaining_milliseconds
            // 60_000
        )

        remaining_milliseconds %= 60_000

        whole_seconds = (
            remaining_milliseconds
            // 1000
        )

        milliseconds = (
            remaining_milliseconds
            % 1000
        )

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{whole_seconds:02d},"
            f"{milliseconds:03d}"
        )