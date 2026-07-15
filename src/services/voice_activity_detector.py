from typing import Any

import numpy as np
import soundfile as sf

from silero_vad import get_speech_timestamps, load_silero_vad


class VoiceActivityDetector:
    """Detect human speech regions in mono 16 kHz audio."""

    def __init__(self) -> None:
        self.model = load_silero_vad()

    def detect(self, audio_file: str) -> list[dict[str, Any]]:
        audio, sample_rate = sf.read(
            audio_file,
            dtype="float32",
            always_2d=False,
        )

        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        audio = np.asarray(audio, dtype=np.float32)

        speech_segments = get_speech_timestamps(
            audio,
            self.model,
            sampling_rate=sample_rate,
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=700,
            speech_pad_ms=400,
            return_seconds=False,
        )

        return speech_segments