import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.audio_analyzer import AudioAnalyzer
from src.services.audio_extractor import AudioExtractor
from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.highlight_feature_extractor import HighlightFeatureExtractor
from src.services.highlight_scorer import HighlightScorer
from src.services.highlight_selector import HighlightSelector
from src.services.motion_analyzer import MotionAnalyzer
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.voice_activity_detector import VoiceActivityDetector
from src.services.video_loader import VideoLoader
from src.services.highlight_overlap_resolver import HighlightOverlapResolver


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)

AUDIO_FILE = "temp/audio.wav"
SPEECH_FOLDER = "temp/speech_chunks"


def main() -> None:
    print("=" * 60)
    print("Highlight Candidate Verification")
    print("=" * 60)

    video_loader = VideoLoader()
    video_info = video_loader.load(VIDEO_FILE)

    audio_extractor = AudioExtractor()
    audio_extractor.extract(
        input_video=VIDEO_FILE,
        output_audio=AUDIO_FILE,
    )

    vad = VoiceActivityDetector()
    speech_segments = vad.detect(AUDIO_FILE)

    speech_chunk_extractor = SpeechChunkExtractor()
    speech_chunks = speech_chunk_extractor.extract(
        input_audio=AUDIO_FILE,
        speech_segments=speech_segments,
        output_folder=SPEECH_FOLDER,
    )

    transcription_pipeline = TranscriptionPipeline()
    transcript_segments = transcription_pipeline.transcribe(
        speech_chunks
    )

    scene_detector = SceneDetector()
    scenes = scene_detector.detect(VIDEO_FILE)

    scene_mapper = SceneTranscriptMapper()
    scene_analyses = scene_mapper.map(
        scenes=scenes,
        transcript_segments=transcript_segments,
    )

    motion_analyzer = MotionAnalyzer()
    motion_features = motion_analyzer.analyze(
        video_file=VIDEO_FILE,
        scenes=scenes,
    )

    audio_analyzer = AudioAnalyzer()
    audio_features = audio_analyzer.analyze(
        audio_file=AUDIO_FILE,
        scenes=scenes,
    )

    feature_extractor = HighlightFeatureExtractor()
    highlight_features = feature_extractor.extract(
        scene_analyses=scene_analyses,
        motion_features=motion_features,
        audio_features=audio_features,
    )

    scorer = HighlightScorer()
    highlight_scores = scorer.score(highlight_features)

    selector = HighlightSelector()
    candidates = selector.select(
        scores=highlight_scores,
        video_duration_seconds=video_info.duration_seconds,
    )
    overlap_resolver = HighlightOverlapResolver()

    candidates = overlap_resolver.resolve(candidates)
    print()
    print(f"Candidates: {len(candidates)}")
    print()

    for candidate in candidates:
        features = candidate.score.features

        print("-" * 60)
        print(f"Rank       : {candidate.rank}")
        print(
            f"Clip       : "
            f"{candidate.start_seconds:.2f}s "
            f"-> {candidate.end_seconds:.2f}s"
        )
        print(
            f"Duration   : "
            f"{candidate.duration_seconds:.2f}s"
        )
        print(
            f"Final Score: "
            f"{candidate.score.final_score:.4f}"
        )
        print(
            f"Scene      : "
            f"{features.scene_start_seconds:.2f}s "
            f"-> {features.scene_end_seconds:.2f}s"
        )
        print(
            f"Transcript : "
            f"{features.transcript_text or '[NO SPEECH]'}"
        )


if __name__ == "__main__":
    main()