import sys
from pathlib import Path

import truststore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

truststore.inject_into_ssl()

from funasr import AutoModel


MODEL_NAME = "FunAudioLLM/Fun-ASR-MLT-Nano-2512"
AUDIO_FILE = "temp/speech_chunks/speech_001.wav"


print("=" * 60)
print("FunASR Hindi Verification")
print("=" * 60)

print()
print("Loading model...")

model = AutoModel(
    model=MODEL_NAME,
    hub="hf",
    trust_remote_code=True,
    remote_code="./model.py",
    device="cpu",
)

print("Model loaded successfully.")

print()
print("Transcribing...")

result = model.generate(
    input=[AUDIO_FILE],
    cache={},
    batch_size=1,
    language="印地语",
    itn=True,
    llm_kwargs={"do_sample": False},
)

print()
print("Result:")
print(result)

if result:
    print()
    print("Transcript:")
    print(result[0].get("text", ""))