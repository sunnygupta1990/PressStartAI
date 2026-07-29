from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class HighlightFeatures:
    """Features extracted from one video scene."""

    scene_start_seconds: float
    scene_end_seconds: float
    scene_duration_seconds: float

    transcript_text: str
    has_speech: bool

    speech_character_count: int
    speech_word_count: int

    average_motion_score: float
    maximum_motion_score: float

    average_audio_rms: float
    maximum_audio_rms: float