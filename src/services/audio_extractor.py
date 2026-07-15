from pathlib import Path

import ffmpeg


class AudioExtractor:

    def extract(
        self,
        input_video: str,
        output_audio: str,
        sample_rate: int = 16000,
    ) -> str:

        output_path = Path(output_audio)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        (
            ffmpeg
            .input(input_video)
            .output(
                output_audio,
                ac=1,
                ar=sample_rate,
                vn=None,
                acodec="pcm_s16le",
            )
            .overwrite_output()
            .run(quiet=True)
        )

        return str(output_path)