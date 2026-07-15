from dataclasses import dataclass
from pathlib import Path

import torch
import truststore
from qwen_asr import Qwen3ASRModel

from src.services.asr.base_asr import BaseASR


@dataclass(slots=True, frozen=True)
class ASRResult:
    """Result returned by a speech recognition engine."""

    language: str
    text: str
    audio_file: str


class QwenASR(BaseASR):
    """CPU-based Qwen3 ASR implementation."""

    MODEL_NAME = "Qwen/Qwen3-ASR-0.6B"

    def __init__(self) -> None:
        truststore.inject_into_ssl()

        self.model = Qwen3ASRModel.from_pretrained(
            self.MODEL_NAME,
            dtype=torch.float32,
            device_map="cpu",
            max_inference_batch_size=1,
            max_new_tokens=256,
        )

    def transcribe(self, audio_file: str) -> ASRResult:
        audio_path = Path(audio_file)

        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Audio file does not exist: {audio_path}"
            )

        results = self.model.transcribe(
            audio=str(audio_path),
            language=None,
        )

        if not results:
            return ASRResult(
                language="unknown",
                text="",
                audio_file=str(audio_path),
            )

        result = results[0]

        return ASRResult(
            language=str(result.language),
            text=str(result.text).strip(),
            audio_file=str(audio_path),
        )