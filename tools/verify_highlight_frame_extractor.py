import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.highlight_frame_extractor import HighlightFrameExtractor


HIGHLIGHT_FILE = (
    r"temp\final_highlights\highlight_001.mp4"
)

OUTPUT_FOLDER = "temp/highlight_frames"


def create_highlight() -> GeneratedHighlight:
    transcript_text = (
        "बाग बाग बाग बाग गलत हक्किया चलो "
        "उस पेल ने बचा लिया मेरे को कभी नहीं हाँ"
    )

    features = HighlightFeatures(
        scene_start_seconds=21.00,
        scene_end_seconds=26.17,
        scene_duration_seconds=5.17,
        transcript_text=transcript_text,
        has_speech=True,
        speech_character_count=len(transcript_text),
        speech_word_count=len(transcript_text.split()),
        average_motion_score=12.4827,
        maximum_motion_score=48.5669,
        average_audio_rms=0.203682,
        maximum_audio_rms=0.372899,
    )

    score = HighlightScore(
        features=features,
        speech_score=1.0,
        motion_score=0.6315,
        audio_score=1.0,
        final_score=0.8342,
    )

    candidate = HighlightCandidate(
        start_seconds=18.00,
        end_seconds=29.17,
        rank=1,
        score=score,
    )

    return GeneratedHighlight(
        file_path=HIGHLIGHT_FILE,
        candidate=candidate,
    )


def main() -> None:
    highlight = create_highlight()

    extractor = HighlightFrameExtractor(
        frame_count=5,
    )

    frame_files = extractor.extract(
        highlight=highlight,
        output_folder=OUTPUT_FOLDER,
    )

    print("=" * 60)
    print("Highlight Frame Extractor Verification")
    print("=" * 60)

    print(f"Generated Frames: {len(frame_files)}")
    print()

    for frame_file in frame_files:
        path = Path(frame_file)

        print("-" * 60)
        print(f"File   : {path}")
        print(f"Exists : {path.is_file()}")

        if path.is_file():
            print(
                f"Size   : "
                f"{path.stat().st_size / 1024:.2f} KB"
            )


if __name__ == "__main__":
    main()