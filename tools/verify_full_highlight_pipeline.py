import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.audio_analyzer import AudioAnalyzer
from src.services.audio_extractor import AudioExtractor
from src.services.highlight_analysis_combiner import HighlightAnalysisCombiner
from src.services.highlight_clip_generator import HighlightClipGenerator
from src.services.highlight_feature_extractor import HighlightFeatureExtractor
from src.services.highlight_overlap_resolver import HighlightOverlapResolver
from src.services.highlight_reasoner import HighlightReasoner
from src.services.highlight_scorer import HighlightScorer
from src.services.highlight_selector import HighlightSelector
from src.services.motion_analyzer import MotionAnalyzer
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.video_loader import VideoLoader
from src.services.voice_activity_detector import VoiceActivityDetector


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)

AUDIO_FILE = "temp/audio.wav"
SPEECH_FOLDER = "temp/speech_chunks"
HIGHLIGHT_FOLDER = "temp/final_highlights"


def main() -> None:
    print("=" * 60)
    print("PressStartAI Full Highlight Pipeline")
    print("=" * 60)

    print()
    print("[1/13] Loading video...")

    video_loader = VideoLoader()
    video_info = video_loader.load(VIDEO_FILE)

    print()
    print("[2/13] Extracting audio...")

    audio_extractor = AudioExtractor()
    audio_extractor.extract(
        input_video=VIDEO_FILE,
        output_audio=AUDIO_FILE,
    )

    print()
    print("[3/13] Detecting speech...")

    vad = VoiceActivityDetector()
    speech_segments = vad.detect(AUDIO_FILE)

    print()
    print("[4/13] Creating speech chunks...")

    speech_chunk_extractor = SpeechChunkExtractor()
    speech_chunks = speech_chunk_extractor.extract(
        input_audio=AUDIO_FILE,
        speech_segments=speech_segments,
        output_folder=SPEECH_FOLDER,
    )

    print()
    print("[5/13] Transcribing commentary...")

    transcription_pipeline = TranscriptionPipeline()
    transcript_segments = transcription_pipeline.transcribe(
        speech_chunks
    )

    print()
    print("[6/13] Detecting scenes...")

    scene_detector = SceneDetector()
    scenes = scene_detector.detect(VIDEO_FILE)

    print()
    print("[7/13] Mapping commentary to scenes...")

    scene_mapper = SceneTranscriptMapper()
    scene_analyses = scene_mapper.map(
        scenes=scenes,
        transcript_segments=transcript_segments,
    )

    print()
    print("[8/13] Analyzing motion...")

    motion_analyzer = MotionAnalyzer()
    motion_features = motion_analyzer.analyze(
        video_file=VIDEO_FILE,
        scenes=scenes,
    )

    print()
    print("[9/13] Analyzing audio intensity...")

    audio_analyzer = AudioAnalyzer()
    audio_features = audio_analyzer.analyze(
        audio_file=AUDIO_FILE,
        scenes=scenes,
    )

    print()
    print("[10/13] Scoring highlight scenes...")

    feature_extractor = HighlightFeatureExtractor()
    highlight_features = feature_extractor.extract(
        scene_analyses=scene_analyses,
        motion_features=motion_features,
        audio_features=audio_features,
    )

    scorer = HighlightScorer()
    highlight_scores = scorer.score(
        highlight_features
    )

    print()
    print("[11/13] Selecting highlight candidates...")

    selector = HighlightSelector()
    candidates = selector.select(
        scores=highlight_scores,
        video_duration_seconds=video_info.duration_seconds,
    )

    overlap_resolver = HighlightOverlapResolver()
    candidates = overlap_resolver.resolve(candidates)

    print()
    print("[12/13] Generating highlight clips...")

    clip_generator = HighlightClipGenerator()
    generated_highlights = clip_generator.generate(
        video_file=VIDEO_FILE,
        candidates=candidates,
        output_folder=HIGHLIGHT_FOLDER,
    )

    print()
    print("[13/13] Running local AI reasoning...")

    reasoner = HighlightReasoner()
    reasoning_results = reasoner.reason(
        generated_highlights
    )

    combiner = HighlightAnalysisCombiner()
    analyzed_highlights = combiner.combine(
        highlights=generated_highlights,
        reasoning_results=reasoning_results,
    )

    print()
    print("=" * 60)
    print("FINAL ANALYZED HIGHLIGHTS")
    print("=" * 60)

    print(
        f"Analyzed Highlights: "
        f"{len(analyzed_highlights)}"
    )

    for highlight in analyzed_highlights:
        print()
        print("-" * 60)
        print(f"Rank        : {highlight.rank}")
        print(f"File        : {highlight.file_path}")
        print(
            f"Timeline    : "
            f"{highlight.start_seconds:.2f}s "
            f"-> {highlight.end_seconds:.2f}s"
        )
        print(
            f"Duration    : "
            f"{highlight.duration_seconds:.2f}s"
        )
        print(
            f"Score       : "
            f"{highlight.final_score:.4f}"
        )
        print(
            f"Interesting : "
            f"{highlight.is_interesting}"
        )
        print(f"Category    : {highlight.category}")
        print(
            f"Confidence  : "
            f"{highlight.confidence:.4f}"
        )
        print(
            f"Transcript  : "
            f"{highlight.transcript_text or '[NO SPEECH]'}"
        )
        print(f"Reason      : {highlight.reason}")


if __name__ == "__main__":
    main()