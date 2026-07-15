import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.highlight_frame_extractor import HighlightFrameExtractor
from src.services.visual_highlight_reasoner import VisualHighlightReasoner


HIGHLIGHT_FILE = (
    r"temp\final_highlights\highlight_001.mp4"
)

FRAME_FOLDER = "temp/highlight_frames"


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

    frame_extractor = HighlightFrameExtractor(
        frame_count=5,
    )

    frame_files = frame_extractor.extract(
        highlight=highlight,
        output_folder=FRAME_FOLDER,
    )

    reasoner = VisualHighlightReasoner()

    result = reasoner.reason(
        highlight=highlight,
        frame_files=frame_files,
    )

    print("=" * 60)
    print("Visual Highlight Reasoner Verification")
    print("=" * 60)

    print(f"Rank              : {result.rank}")
    print(f"Visual Event      : {result.visual_event}")
    print(f"Action Level      : {result.action_level}")
    print(f"Danger Level      : {result.danger_level}")
    print(
        f"Looks Interesting : "
        f"{result.looks_interesting}"
    )
    print(
        f"Confidence        : "
        f"{result.confidence:.4f}"
    )
    print(f"Reason            : {result.reason}")


if __name__ == "__main__":
    main()