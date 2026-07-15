import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.scene_detector import SceneDetector


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)


print("=" * 60)
print("Scene Detector Verification")
print("=" * 60)

detector = SceneDetector()

scenes = detector.detect(VIDEO_FILE)

print()
print("Scenes Found:", len(scenes))
print()

for index, scene in enumerate(scenes, start=1):
    print(
        f"{index}. "
        f"{scene.start_seconds:.2f}s -> "
        f"{scene.end_seconds:.2f}s | "
        f"Duration={scene.duration_seconds:.2f}s"
    )