import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.caption_renderer import CaptionRenderer


VIDEO_FILE = "temp/verify_shorts/short_001.mp4"
SUBTITLE_FILE = "temp/verify_captions/captions.srt"
OUTPUT_FILE = "temp/verify_captioned_short/short_001_captioned.mp4"


def read_video_dimensions(
    video_file: str,
) -> tuple[int, int]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        video_file,
    ]

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed: {process.stderr}"
        )

    width_text, height_text = (
        process.stdout.strip().split(
            "x",
            maxsplit=1,
        )
    )

    return int(width_text), int(height_text)


def main() -> None:
    print("=" * 60)
    print("Caption Renderer Verification")
    print("=" * 60)

    renderer = CaptionRenderer()

    output_file = renderer.render(
        video_file=VIDEO_FILE,
        subtitle_file=SUBTITLE_FILE,
        output_file=OUTPUT_FILE,
    )

    output_path = Path(
        output_file
    )

    if not output_path.is_file():
        raise RuntimeError(
            "Captioned Short was not created."
        )

    width, height = read_video_dimensions(
        output_file
    )

    print(
        f"File       : "
        f"{output_file}"
    )

    print(
        f"Dimensions : "
        f"{width}x{height}"
    )

    print(
        f"Size       : "
        f"{output_path.stat().st_size / 1024 / 1024:.2f} MB"
    )

    if width != 1080 or height != 1920:
        raise RuntimeError(
            "Captioned Short dimensions are invalid."
        )

    print()
    print(
        "CaptionRenderer verification successful."
    )


if __name__ == "__main__":
    main()