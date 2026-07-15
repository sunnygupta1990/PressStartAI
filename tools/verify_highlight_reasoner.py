import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_candidate import HighlightCandidate
from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore
from src.services.highlight_reasoner import HighlightReasoner


def create_highlight(
    rank: int,
    start_seconds: float,
    end_seconds: float,
    final_score: float,
    transcript_text: str,
) -> GeneratedHighlight:
    features = HighlightFeatures(
        scene_start_seconds=start_seconds,
        scene_end_seconds=end_seconds,
        scene_duration_seconds=end_seconds - start_seconds,
        transcript_text=transcript_text,
        has_speech=bool(transcript_text),
        speech_character_count=len(transcript_text),
        speech_word_count=len(transcript_text.split()),
        average_motion_score=0.0,
        maximum_motion_score=0.0,
        average_audio_rms=0.0,
        maximum_audio_rms=0.0,
    )

    score = HighlightScore(
        features=features,
        speech_score=0.0,
        motion_score=0.0,
        audio_score=0.0,
        final_score=final_score,
    )

    candidate = HighlightCandidate(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        rank=rank,
        score=score,
    )

    return GeneratedHighlight(
        file_path=f"temp/highlight_{rank:03d}.mp4",
        candidate=candidate,
    )


def main() -> None:
    highlights = [
        create_highlight(
            rank=1,
            start_seconds=18.00,
            end_seconds=29.17,
            final_score=0.8342,
            transcript_text=(
                "बाग बाग बाग बाग गलत हक्किया चलो "
                "उस पेल ने बचा लिया मेरे को कभी नहीं हाँ"
            ),
        ),
        create_highlight(
            rank=4,
            start_seconds=0.00,
            end_seconds=12.17,
            final_score=0.4806,
            transcript_text=(
                "जो आती गलत हो गई हर इससे सामने"
            ),
        ),
    ]

    reasoner = HighlightReasoner()

    results = reasoner.reason(highlights)

    print("=" * 60)
    print("Highlight Reasoner Verification")
    print("=" * 60)

    print(f"Results: {len(results)}")
    print()

    for result in results:
        print("-" * 60)
        print(f"Rank          : {result.rank}")
        print(f"Interesting   : {result.is_interesting}")
        print(f"Category      : {result.category}")
        print(f"Confidence    : {result.confidence:.4f}")
        print(f"Reason        : {result.reason}")


if __name__ == "__main__":
    main()