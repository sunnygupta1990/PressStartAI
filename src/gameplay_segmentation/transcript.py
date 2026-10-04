
from __future__ import annotations

import subprocess
from pathlib import Path


class CandidateTranscriber:
    """Transcribe only candidates that contain detected speech."""

    def __init__(self) -> None:
        self._asr = None

    def transcribe(self, video_file: str, start: float, end: float, work_dir: str) -> str:
        try:
            from src.services.asr.qwen_asr import QwenASR
        except Exception:
            return ""
        audio = Path(work_dir) / f"candidate_{start:.3f}_{end:.3f}.wav"
        audio.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start:.3f}", "-i", video_file, "-t", f"{end-start:.3f}",
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return ""
        if self._asr is None:
            self._asr = QwenASR()
        try:
            return self._asr.transcribe(str(audio)).text.strip()
        finally:
            audio.unlink(missing_ok=True)


def slice_transcript(transcript, start_time, end_time):
    """Return transcript text overlapping [start_time, end_time]."""
    if not transcript:
        return ""
    parts = []
    for item in transcript:
        if isinstance(item, dict):
            s = float(item.get("start", item.get("start_time", 0.0)))
            e = float(item.get("end", item.get("end_time", s)))
            txt = str(item.get("text", "")).strip()
        else:
            s = float(getattr(item, "start", getattr(item, "start_time", 0.0)))
            e = float(getattr(item, "end", getattr(item, "end_time", s)))
            txt = str(getattr(item, "text", "")).strip()
        if e > start_time and s < end_time and txt:
            parts.append(txt)
    return " ".join(parts)
