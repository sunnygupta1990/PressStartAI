import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.highlight_frame_extractor import HighlightFrameExtractor


HIGHLIGHT_FILE = (
    "temp/final_highlights/highlight_001.mp4"
)

OUTPUT_FOLDER = (
    "temp/verify_resized_frames"
)


def main() -> None:
    print("=" * 60)
    print("Highlight Frame Extractor Resize Verification")
    print("=" * 60)

    features = HighlightFeatures(
        scene_start_seconds=21.0,
        scene_end_seconds=26.17,
        scene_duration_seconds=5.17,
        transcript_text="Verification transcript",
        has_speech=True,
        speech_character_count=23,
        speech_word_count=2,
        average_motion_score=12.0,
        maximum_motion_score=48.0,
        average_audio_rms=0.20,
        maximum_audio_rms=0.37,
    )

    score = HighlightScore(
        features=features,
        speech_score=1.0,
        motion_score=0.63,
        audio_score=1.0,
        final_score=0.83,
    )

    candidate = HighlightCandidate(
        start_seconds=18.0,
        end_seconds=29.17,
        rank=1,
        score=score,
    )

    highlight = GeneratedHighlight(
        file_path=HIGHLIGHT_FILE,
        candidate=candidate,
    )

    extractor = HighlightFrameExtractor(
        frame_count=3,
        maximum_frame_width=768,
    )

    frame_files = extractor.extract(
        highlight=highlight,
        output_folder=OUTPUT_FOLDER,
    )

    print(
        f"Frames Generated : "
        f"{len(frame_files)}"
    )

    if len(frame_files) != 3:
        raise RuntimeError(
            "Expected exactly three frames."
        )

    for frame_file in frame_files:
        frame = cv2.imread(
            frame_file
        )

        if frame is None:
            raise RuntimeError(
                f"Unable to read frame: {frame_file}"
            )

        height, width = frame.shape[:2]

        print(
            f"{frame_file} : "
            f"{width}x{height}"
        )

        if width > 768:
            raise RuntimeError(
                "Extracted frame exceeds maximum width."
            )

    print()
    print(
        "HighlightFrameExtractor resize "
        "verification successful."
    )


if __name__ == "__main__":
    main()