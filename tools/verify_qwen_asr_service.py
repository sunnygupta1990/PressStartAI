import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.asr.qwen_asr import QwenASR


CHUNKS_FOLDER = Path("temp/speech_chunks")


print("=" * 60)
print("Qwen ASR Production Service Verification")
print("=" * 60)

engine = QwenASR()

audio_files = sorted(CHUNKS_FOLDER.glob("speech_*.wav"))

print()
print(f"Speech chunks found: {len(audio_files)}")
print()

for index, audio_file in enumerate(audio_files, start=1):
    print("-" * 60)
    print(f"Chunk {index}: {audio_file.name}")

    result = engine.transcribe(str(audio_file))

    print("Language :", result.language)
    print("Transcript:", result.text)

print()
print("=" * 60)
print("Verification completed")
print("=" * 60)