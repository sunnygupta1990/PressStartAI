from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class MotionFeatures:
    """Motion measurements for one video scene."""

    scene_start_seconds: float
    scene_end_seconds: float

    average_motion_score: float
    maximum_motion_score: float