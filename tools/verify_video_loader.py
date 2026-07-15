import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.video_loader import VideoLoader

print("=" * 60)
print("Video Loader Verification")
print("=" * 60)

video = input("Enter full path of a video:\n").strip()

loader = VideoLoader()
info = loader.load(video)

print()
print(info)