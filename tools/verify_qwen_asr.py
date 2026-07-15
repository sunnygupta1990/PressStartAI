import sys
from pathlib import Path

import torch
import truststore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

truststore.inject_into_ssl()

from qwen_asr import Qwen3ASRModel


MODEL_NAME = "Qwen/Qwen3-ASR-0.6B"
AUDIO_FILE = "temp/speech_chunks/speech_001.wav"


print("=" * 60)
print("Qwen3-ASR Hindi Verification")
print("=" * 60)

print()
print("Loading Qwen3-ASR model on CPU...")

model = Qwen3ASRModel.from_pretrained(
    MODEL_NAME,
    dtype=torch.float32,
    device_map="cpu",
    max_inference_batch_size=1,
    max_new_tokens=128,
)

print("Model loaded successfully.")

print()
print("Transcribing...")

results = model.transcribe(
    audio=AUDIO_FILE,
    language="Hindi",
)

print()
print("Result:")

for result in results:
    print("Language :", result.language)
    print("Transcript:", result.text)