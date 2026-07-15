import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.audio_analyzer import AudioAnalyzer
from src.services.highlight_feature_extractor import HighlightFeatureExtractor
from src.services.highlight_scorer import HighlightScorer
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
print("Highlight Scorer Verification")
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

audio_analyzer = AudioAnalyzer()

audio_features = audio_analyzer.analyze(
    audio_file=AUDIO_FILE,
    scenes=scenes,
)

feature_extractor = HighlightFeatureExtractor()

features = feature_extractor.extract(
    scene_analyses=scene_analyses,
    motion_features=motion_features,
    audio_features=audio_features,
)

scorer = HighlightScorer()

scores = scorer.score(features)

print()
print("Ranked Highlights:", len(scores))
print()

for rank, score in enumerate(scores, start=1):
    feature = score.features

    print("-" * 60)
    print(f"Rank {rank}")
    print(
        f"Scene: "
        f"{feature.scene_start_seconds:.2f}s -> "
        f"{feature.scene_end_seconds:.2f}s"
    )
    print(f"Speech Score: {score.speech_score:.4f}")
    print(f"Motion Score: {score.motion_score:.4f}")
    print(f"Audio Score : {score.audio_score:.4f}")
    print(f"Final Score : {score.final_score:.4f}")
    print(
        "Transcript  :",
        feature.transcript_text or "[NO SPEECH]",
    )