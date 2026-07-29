from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class VideoInfo:
    file_path: str
    file_name: str

    duration_seconds: float

    width: int
    height: int
    fps: float

    video_codec: str
    audio_codec: str

    video_bitrate: int
    audio_bitrate: int

    file_size: int

    rotation: int = 0