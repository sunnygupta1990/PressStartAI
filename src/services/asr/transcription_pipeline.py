from src.models.asr_segment import ASRSegment
from src.models.speech_chunk import SpeechChunk
from src.services.asr.qwen_asr import QwenASR


class TranscriptionPipeline:
    """Transcribe speech chunks and restore original video timestamps."""

    def __init__(self) -> None:
        self.asr = QwenASR()

    def transcribe(
        self,
        speech_chunks: list[SpeechChunk],
    ) -> list[ASRSegment]:
        transcript: list[ASRSegment] = []

        for chunk in speech_chunks:
            result = self.asr.transcribe(chunk.file_path)

            if not result.text:
                continue

            transcript.append(
                ASRSegment(
                    start_seconds=chunk.start_seconds,
                    end_seconds=chunk.end_seconds,
                    language=result.language,
                    text=result.text,
                )
            )

        return transcript