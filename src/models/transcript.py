from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    avg_logprob: float
    no_speech_probability: float


@dataclass(slots=True, frozen=True)
class Transcript:
    language: str
    duration: float
    segments: list[TranscriptSegment]