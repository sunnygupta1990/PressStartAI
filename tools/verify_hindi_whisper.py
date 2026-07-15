import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.transcript_engine import TranscriptEngine

print("=" * 60)
print("Hindi Whisper Verification")
print("=" * 60)

engine = TranscriptEngine()

segments, info = engine.model.transcribe(
    "temp/speech_chunks/speech_001.wav",
    language="hi",
    beam_size=5,
    temperature=0,
    condition_on_previous_text=False,
    vad_filter=False,
)

print()
print("Detected Language:", info.language)
print()

for segment in segments:
    print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text}")