import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.voice_activity_detector import VoiceActivityDetector

print("=" * 60)
print("Voice Activity Detection Verification")
print("=" * 60)

vad = VoiceActivityDetector()

speech = vad.detect("temp/audio.wav")

print()

print("Speech Segments Found:", len(speech))

print()

for i, segment in enumerate(speech):

    print(
        f"{i+1}. "
        f"Start={segment['start']} "
        f"End={segment['end']}"
    )