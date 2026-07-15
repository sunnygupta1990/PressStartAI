import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.audio_analyzer import AudioAnalyzer
from src.services.audio_extractor import AudioExtractor
from src.services.final_highlight_combiner import FinalHighlightCombiner
from src.services.final_highlight_exporter import FinalHighlightExporter
from src.services.final_highlight_selector import FinalHighlightSelector
from src.services.highlight_analysis_combiner import HighlightAnalysisCombiner
from src.services.highlight_clip_generator import HighlightClipGenerator
from src.services.highlight_feature_extractor import HighlightFeatureExtractor
from src.services.highlight_frame_extractor import HighlightFrameExtractor
from src.services.highlight_fusion_reasoner import HighlightFusionReasoner
from src.services.highlight_overlap_resolver import HighlightOverlapResolver
from src.services.highlight_reasoner import HighlightReasoner
from src.services.highlight_scorer import HighlightScorer
from src.services.highlight_selector import HighlightSelector
from src.services.motion_analyzer import MotionAnalyzer
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.video_loader import VideoLoader
from src.services.visual_highlight_reasoner import VisualHighlightReasoner
from src.services.voice_activity_detector import VoiceActivityDetector


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)

AUDIO_FILE = "temp/audio.wav"
SPEECH_FOLDER = "temp/speech_chunks"
HIGHLIGHT_FOLDER = "temp/final_highlights"
FRAME_FOLDER = "temp/final_highlight_frames"
OUTPUT_FOLDER = "output/highlights"


def main() -> None:
    print("=" * 60)
    print("PressStartAI Full Multimodal Highlight Pipeline")
    print("=" * 60)

    print()
    print("[1/19] Loading video...")

    video_loader = VideoLoader()
    video_info = video_loader.load(VIDEO_FILE)

    print()
    print("[2/19] Extracting audio...")

    audio_extractor = AudioExtractor()
    audio_extractor.extract(
        input_video=VIDEO_FILE,
        output_audio=AUDIO_FILE,
    )

    print()
    print("[3/19] Detecting speech...")

    vad = VoiceActivityDetector()
    speech_segments = vad.detect(AUDIO_FILE)

    print()
    print("[4/19] Creating speech chunks...")

    speech_chunk_extractor = SpeechChunkExtractor()
    speech_chunks = speech_chunk_extractor.extract(
        input_audio=AUDIO_FILE,
        speech_segments=speech_segments,
        output_folder=SPEECH_FOLDER,
    )

    print()
    print("[5/19] Transcribing commentary...")

    transcription_pipeline = TranscriptionPipeline()
    transcript_segments = transcription_pipeline.transcribe(
        speech_chunks
    )

    print()
    print("[6/19] Detecting scenes...")

    scene_detector = SceneDetector()
    scenes = scene_detector.detect(VIDEO_FILE)

    print()
    print("[7/19] Mapping commentary to scenes...")

    scene_mapper = SceneTranscriptMapper()
    scene_analyses = scene_mapper.map(
        scenes=scenes,
        transcript_segments=transcript_segments,
    )

    print()
    print("[8/19] Analyzing motion...")

    motion_analyzer = MotionAnalyzer()
    motion_features = motion_analyzer.analyze(
        video_file=VIDEO_FILE,
        scenes=scenes,
    )

    print()
    print("[9/19] Analyzing audio intensity...")

    audio_analyzer = AudioAnalyzer()
    audio_features = audio_analyzer.analyze(
        audio_file=AUDIO_FILE,
        scenes=scenes,
    )

    print()
    print("[10/19] Scoring highlight scenes...")

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
    print("[11/19] Selecting highlight candidates...")

    selector = HighlightSelector()
    candidates = selector.select(
        scores=highlight_scores,
        video_duration_seconds=video_info.duration_seconds,
    )

    overlap_resolver = HighlightOverlapResolver()
    candidates = overlap_resolver.resolve(
        candidates
    )

    print()
    print("[12/19] Generating highlight clips...")

    clip_generator = HighlightClipGenerator()
    generated_highlights = clip_generator.generate(
        video_file=VIDEO_FILE,
        candidates=candidates,
        output_folder=HIGHLIGHT_FOLDER,
    )

    print()
    print("[13/19] Running commentary AI reasoning...")

    commentary_reasoner = HighlightReasoner()
    commentary_results = commentary_reasoner.reason(
        generated_highlights
    )

    analysis_combiner = HighlightAnalysisCombiner()
    analyzed_highlights = analysis_combiner.combine(
        highlights=generated_highlights,
        reasoning_results=commentary_results,
    )

    print()
    print("[14/19] Extracting representative frames...")

    frame_extractor = HighlightFrameExtractor(
        frame_count=5,
    )

    highlight_frames: dict[int, list[str]] = {}

    for highlight in generated_highlights:
        frame_files = frame_extractor.extract(
            highlight=highlight,
            output_folder=FRAME_FOLDER,
        )

        highlight_frames[
            highlight.rank
        ] = frame_files

    print()
    print("[15/19] Running visual AI reasoning...")

    visual_reasoner = VisualHighlightReasoner()

    visual_results = {}

    for highlight in generated_highlights:
        frame_files = highlight_frames.get(
            highlight.rank,
            [],
        )

        visual_result = visual_reasoner.reason(
            highlight=highlight,
            frame_files=frame_files,
        )

        visual_results[
            highlight.rank
        ] = visual_result

    print()
    print("[16/19] Fusing multimodal AI decisions...")

    fusion_reasoner = HighlightFusionReasoner()

    fusion_results = []

    for analyzed_highlight in analyzed_highlights:
        visual_result = visual_results.get(
            analyzed_highlight.rank
        )

        if visual_result is None:
            continue

        fusion_result = fusion_reasoner.reason(
            analyzed_highlight=analyzed_highlight,
            visual_reasoning=visual_result,
        )

        fusion_results.append(
            fusion_result
        )

    print()
    print("[17/19] Selecting final approved highlights...")

    final_selector = FinalHighlightSelector(
        minimum_confidence=0.70,
    )

    approved_results = final_selector.select(
        fusion_results
    )

    print()
    print("[18/19] Linking approved decisions to clips...")

    final_combiner = FinalHighlightCombiner()

    final_highlights = final_combiner.combine(
        highlights=generated_highlights,
        approved_results=approved_results,
    )

    print()
    print("[19/19] Exporting final highlight package...")

    exporter = FinalHighlightExporter()

    exported_files = exporter.export(
        highlights=final_highlights,
        output_folder=OUTPUT_FOLDER,
    )

    print()
    print("=" * 60)
    print("FINAL EXPORTED HIGHLIGHTS")
    print("=" * 60)

    print(
        f"Exported Highlights: "
        f"{len(exported_files)}"
    )

    for highlight, exported_file in zip(
        final_highlights,
        exported_files,
        strict=True,
    ):
        print()
        print("-" * 60)
        print(f"Rank             : {highlight.rank}")
        print(f"File             : {exported_file}")
        print(f"Category         : {highlight.category}")
        print(
            f"Confidence       : "
            f"{highlight.confidence:.4f}"
        )
        print(
            f"Event Summary    : "
            f"{highlight.event_summary}"
        )
        print(
            f"Source Timeline  : "
            f"{highlight.start_seconds:.2f}s "
            f"-> {highlight.end_seconds:.2f}s"
        )


if __name__ == "__main__":
    main()