import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.transcript_service import TranscriptService

print("=" * 60)
print("Transcript Verification")
print("=" * 60)

video = input("Enter video path:\n").strip()

service = TranscriptService()

transcript = service.transcribe(video)

print()

print("Language :", transcript.language)
print("Duration :", transcript.duration)
print("Segments :", len(transcript.segments))

print()

for segment in transcript.segments[:10]:
    print(
        f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text}"
    )