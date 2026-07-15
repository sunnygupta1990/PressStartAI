from pathlib import Path

import ffmpeg

from src.models.video_info import VideoInfo


class VideoLoader:
    def load(self, video_path: str) -> VideoInfo:
        path = Path(video_path)

        if not path.exists():
            raise FileNotFoundError(video_path)

        probe = ffmpeg.probe(str(path))

        video_stream = next(
            s for s in probe["streams"]
            if s["codec_type"] == "video"
        )

        audio_stream = next(
            (
                s for s in probe["streams"]
                if s["codec_type"] == "audio"
            ),
            {},
        )

        fps_text = video_stream["r_frame_rate"]
        numerator, denominator = fps_text.split("/")
        fps = float(numerator) / float(denominator)

        return VideoInfo(
            file_path=str(path.resolve()),
            file_name=path.name,
            duration_seconds=float(probe["format"]["duration"]),
            width=int(video_stream["width"]),
            height=int(video_stream["height"]),
            fps=fps,
            video_codec=video_stream.get("codec_name", ""),
            audio_codec=audio_stream.get("codec_name", ""),
            video_bitrate=int(video_stream.get("bit_rate", 0)),
            audio_bitrate=int(audio_stream.get("bit_rate", 0)),
            file_size=int(probe["format"]["size"]),
            rotation=0,
        )