from faster_whisper import WhisperModel


class TranscriptEngine:

    def __init__(
        self,
        model_name="large-v3-turbo",
        device="cpu",
        compute_type="int8",
    ):

        self.model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            download_root="models/cache",
        )

    def transcribe(self, audio_file):

        segments, info = self.model.transcribe(
            audio_file,
            beam_size=5,
            vad_filter=False,
        )

        results = []

        for segment in segments:

            results.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                }
            )

        return info.language, results