import truststore
truststore.inject_into_ssl()

from faster_whisper import WhisperModel

print("=" * 60)
print("Loading Whisper model...")
print("=" * 60)

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
)

print("\n✅ Whisper model loaded successfully.")