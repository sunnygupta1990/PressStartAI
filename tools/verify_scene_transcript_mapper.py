import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.asr.transcription_pipeline import TranscriptionPipeline
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
print("Scene Transcript Mapper Verification")
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

analyses = mapper.map(
    scenes=scenes,
    transcript_segments=transcript,
)

print()
print("Scene Analyses:", len(analyses))
print()

for index, analysis in enumerate(analyses, start=1):
    print("-" * 60)
    print(
        f"Scene {index}: "
        f"{analysis.scene.start_seconds:.2f}s -> "
        f"{analysis.scene.end_seconds:.2f}s"
    )

    print(
        "Transcript:",
        analysis.transcript_text or "[NO SPEECH]",
    )