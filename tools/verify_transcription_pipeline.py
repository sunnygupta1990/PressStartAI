import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.voice_activity_detector import VoiceActivityDetector


print("=" * 60)
print("Full Transcription Pipeline Verification")
print("=" * 60)

vad = VoiceActivityDetector()

speech_segments = vad.detect("temp/audio.wav")

chunk_extractor = SpeechChunkExtractor()

speech_chunks = chunk_extractor.extract(
    input_audio="temp/audio.wav",
    speech_segments=speech_segments,
    output_folder="temp/speech_chunks",
)

pipeline = TranscriptionPipeline()

transcript = pipeline.transcribe(speech_chunks)

print()
print("Transcript Segments:", len(transcript))
print()

for segment in transcript:
    print(
        f"[{segment.start_seconds:.2f} - "
        f"{segment.end_seconds:.2f}] "
        f"[{segment.language}] "
        f"{segment.text}"
    )