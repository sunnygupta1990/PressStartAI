import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.motion_analyzer import MotionAnalyzer
from src.services.scene_detector import SceneDetector


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)


print("=" * 60)
print("Motion Analyzer Verification")
print("=" * 60)

scene_detector = SceneDetector()

scenes = scene_detector.detect(VIDEO_FILE)

motion_analyzer = MotionAnalyzer()

motion_features = motion_analyzer.analyze(
    video_file=VIDEO_FILE,
    scenes=scenes,
)

print()
print("Motion Records:", len(motion_features))
print()

for index, feature in enumerate(motion_features, start=1):
    print("-" * 60)
    print(
        f"Scene {index}: "
        f"{feature.scene_start_seconds:.2f}s -> "
        f"{feature.scene_end_seconds:.2f}s"
    )
    print(
        f"Average Motion: "
        f"{feature.average_motion_score:.4f}"
    )
    print(
        f"Maximum Motion: "
        f"{feature.maximum_motion_score:.4f}"
    )