import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.audio_extractor import AudioExtractor

print("=" * 60)
print("Audio Extractor Verification")
print("=" * 60)

video = input("Enter full path of the video:\n").strip()

extractor = AudioExtractor()

output = extractor.extract(
    input_video=video,
    output_audio="temp/audio.wav",
)

print()
print("Audio extracted successfully.")
print(output)