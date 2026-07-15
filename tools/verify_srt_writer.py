import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.caption_segment import CaptionSegment
from src.services.srt_writer import SRTWriter


OUTPUT_FILE = "temp/verify_captions/captions.srt"


def main() -> None:
    print("=" * 60)
    print("SRT Writer Verification")
    print("=" * 60)

    captions = [
        CaptionSegment(
            start_seconds=0.0,
            end_seconds=2.79,
            text="बाग बाग बाग बाग",
        ),
        CaptionSegment(
            start_seconds=2.79,
            end_seconds=5.59,
            text="गलत हक्किया चलो उस",
        ),
        CaptionSegment(
            start_seconds=5.59,
            end_seconds=8.38,
            text="पेल ने बचा लिया",
        ),
        CaptionSegment(
            start_seconds=8.38,
            end_seconds=11.17,
            text="मेरे को",
        ),
    ]

    writer = SRTWriter()

    output_file = writer.write(
        captions=captions,
        output_file=OUTPUT_FILE,
    )

    output_path = Path(output_file)

    if not output_path.is_file():
        raise RuntimeError(
            "SRT file was not created."
        )

    content = output_path.read_text(
        encoding="utf-8",
    )

    print(f"File : {output_file}")
    print()
    print(content)

    if "00:00:00,000 --> 00:00:02,790" not in content:
        raise RuntimeError(
            "First SRT timestamp is incorrect."
        )

    if "00:00:08,380 --> 00:00:11,170" not in content:
        raise RuntimeError(
            "Last SRT timestamp is incorrect."
        )

    if "बाग बाग बाग बाग" not in content:
        raise RuntimeError(
            "Hindi caption text is missing."
        )

    print(
        "SRTWriter verification successful."
    )


if __name__ == "__main__":
    main()