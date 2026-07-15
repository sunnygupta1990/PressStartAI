import sys
from pathlib import Path

import torch
import truststore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

truststore.inject_into_ssl()

from qwen_asr import Qwen3ASRModel


MODEL_NAME = "Qwen/Qwen3-ASR-0.6B"
CHUNKS_FOLDER = Path("temp/speech_chunks")


print("=" * 60)
print("Qwen3-ASR All Speech Chunks Verification")
print("=" * 60)

print()
print("Loading model...")

model = Qwen3ASRModel.from_pretrained(
    MODEL_NAME,
    dtype=torch.float32,
    device_map="cpu",
    max_inference_batch_size=1,
    max_new_tokens=128,
)

print("Model loaded successfully.")

audio_files = sorted(CHUNKS_FOLDER.glob("speech_*.wav"))

print()
print(f"Speech chunks found: {len(audio_files)}")
print()

for index, audio_file in enumerate(audio_files, start=1):
    print("-" * 60)
    print(f"Chunk {index}: {audio_file.name}")

    results = model.transcribe(
        audio=str(audio_file),
        language=None,
    )

    for result in results:
        print("Language :", result.language)
        print("Transcript:", result.text)

print()
print("=" * 60)
print("Verification completed")
print("=" * 60)