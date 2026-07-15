import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.audio_analyzer import AudioAnalyzer
from src.services.scene_detector import SceneDetector


VIDEO_FILE = (
    r"C:\Users\SunGupta\Downloads\returnal video\1.mp4"
)

AUDIO_FILE = "temp/audio.wav"


print("=" * 60)
print("Audio Analyzer Verification")
print("=" * 60)

scene_detector = SceneDetector()

scenes = scene_detector.detect(VIDEO_FILE)

audio_analyzer = AudioAnalyzer()

audio_features = audio_analyzer.analyze(
    audio_file=AUDIO_FILE,
    scenes=scenes,
)

print()
print("Audio Records:", len(audio_features))
print()

for index, feature in enumerate(
    audio_features,
    start=1,
):
    print("-" * 60)
    print(
        f"Scene {index}: "
        f"{feature.scene_start_seconds:.2f}s -> "
        f"{feature.scene_end_seconds:.2f}s"
    )
    print(
        f"Average RMS: "
        f"{feature.average_rms:.6f}"
    )
    print(
        f"Maximum RMS: "
        f"{feature.maximum_rms:.6f}"
    )