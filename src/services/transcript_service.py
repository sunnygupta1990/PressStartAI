from faster_whisper import WhisperModel

from src.models.transcript import Transcript
from src.models.transcript import TranscriptSegment


class TranscriptService:

    def __init__(self) -> None:

        self.model = WhisperModel(
            "large-v3-turbo",
            device="cpu",
            compute_type="int8",
            download_root="models/cache",
        )

    def transcribe(self, video_path: str) -> Transcript:

        segments, info = self.model.transcribe(
            video_path,
            language="hi",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
            word_timestamps=True,
        )

        transcript_segments = []

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            transcript_segments.append(
                TranscriptSegment(
                    start=segment.start,
                    end=segment.end,
                    text=text,
                    avg_logprob=segment.avg_logprob,
                    no_speech_probability=segment.no_speech_prob,
                )
            )

        return Transcript(
            language=info.language,
            duration=info.duration,
            segments=transcript_segments,
        )