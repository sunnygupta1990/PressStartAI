from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AudioFeatures:
    """Audio intensity measurements for one video scene."""

    scene_start_seconds: float
    scene_end_seconds: float

    average_rms: float
    maximum_rms: float