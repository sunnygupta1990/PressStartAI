from abc import ABC, abstractmethod
from typing import Any


class BaseASR(ABC):
    """Base interface for speech recognition engines."""

    @abstractmethod
    def transcribe(self, audio_file: str) -> Any:
        """Transcribe an audio file."""
        raise NotImplementedError