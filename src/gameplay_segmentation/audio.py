
from __future__ import annotations

import subprocess
from pathlib import Path


class SpeechTimeline:
    """Optional VAD integration. Uses the existing PressStartAI VAD when available."""

    def __init__(self, audio_file: str, sample_rate: int = 16000) -> None:
        self.audio_file = Path(audio_file)
        self.sample_rate = sample_rate

    def detect(self) -> list[tuple[float, float]]:
        try:
            from src.services.voice_activity_detector import VoiceActivityDetector
            raw = VoiceActivityDetector().detect(str(self.audio_file))
            return [
                (float(item["start"]) / self.sample_rate, float(item["end"]) / self.sample_rate)
                for item in raw
            ]
        except Exception:
            return []

    @staticmethod
    def intersects(interval: tuple[float, float], start: float, end: float) -> bool:
        return interval[0] < end and interval[1] > start


def extract_audio(video_file: str, output_file: str) -> str:
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", video_file, "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {result.stderr.strip()}")
    return str(output)
