import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.transcript_engine import TranscriptEngine

print("=" * 60)
print("Transcript Engine Verification")
print("=" * 60)

engine = TranscriptEngine()

language, transcript = engine.transcribe(
    "temp/speech_chunks/speech_001.wav"
)

print()

print("Language:", language)

print()

for line in transcript:
    print(line)