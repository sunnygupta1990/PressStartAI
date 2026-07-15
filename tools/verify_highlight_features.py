import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.highlight_feature_extractor import HighlightFeatureExtractor
from src.services.motion_analyzer import MotionAnalyzer
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.voice_activity_detector import VoiceActivityDetector


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)

AUDIO_FILE = "temp/audio.wav"
CHUNKS_FOLDER = "temp/speech_chunks"


print("=" * 60)
print("Combined Highlight Feature Verification")
print("=" * 60)

vad = VoiceActivityDetector()

speech_segments = vad.detect(AUDIO_FILE)

chunk_extractor = SpeechChunkExtractor()

speech_chunks = chunk_extractor.extract(
    input_audio=AUDIO_FILE,
    speech_segments=speech_segments,
    output_folder=CHUNKS_FOLDER,
)

transcription_pipeline = TranscriptionPipeline()

transcript = transcription_pipeline.transcribe(
    speech_chunks
)

scene_detector = SceneDetector()

scenes = scene_detector.detect(VIDEO_FILE)

mapper = SceneTranscriptMapper()

scene_analyses = mapper.map(
    scenes=scenes,
    transcript_segments=transcript,
)

motion_analyzer = MotionAnalyzer()

motion_features = motion_analyzer.analyze(
    video_file=VIDEO_FILE,
    scenes=scenes,
)

feature_extractor = HighlightFeatureExtractor()

features = feature_extractor.extract(
    scene_analyses=scene_analyses,
    motion_features=motion_features,
)

print()
print("Feature Records:", len(features))
print()

for index, feature in enumerate(features, start=1):
    print("-" * 60)
    print(
        f"Scene {index}: "
        f"{feature.scene_start_seconds:.2f}s -> "
        f"{feature.scene_end_seconds:.2f}s"
    )
    print("Has Speech    :", feature.has_speech)
    print("Word Count    :", feature.speech_word_count)
    print(
        f"Average Motion: "
        f"{feature.average_motion_score:.4f}"
    )
    print(
        f"Maximum Motion: "
        f"{feature.maximum_motion_score:.4f}"
    )
    print(
        "Transcript    :",
        feature.transcript_text or "[NO SPEECH]",
    )
    