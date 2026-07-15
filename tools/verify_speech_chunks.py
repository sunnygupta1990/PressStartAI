import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.voice_activity_detector import VoiceActivityDetector

print("=" * 60)
print("Speech Chunk Verification")
print("=" * 60)

vad = VoiceActivityDetector()

segments = vad.detect("temp/audio.wav")

extractor = SpeechChunkExtractor()

chunks = extractor.extract(
    input_audio="temp/audio.wav",
    speech_segments=segments,
    output_folder="temp/speech_chunks",
)

print()
print("Chunks Created:", len(chunks))
print()

for chunk in chunks:
    print(
        f"{chunk.file_path} | "
        f"{chunk.start_seconds:.2f}s -> "
        f"{chunk.end_seconds:.2f}s"
    )