from pathlib import Path

import numpy as np
import soundfile as sf

from src.models.audio_features import AudioFeatures
from src.models.scene import Scene


class AudioAnalyzer:
    """Measure audio intensity inside detected video scenes."""

    def analyze(
        self,
        audio_file: str,
        scenes: list[Scene],
    ) -> list[AudioFeatures]:
        audio_path = Path(audio_file)

        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Audio file does not exist: {audio_path}"
            )

        audio, sample_rate = sf.read(
            audio_path,
            dtype="float32",
            always_2d=False,
        )

        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        results: list[AudioFeatures] = []

        for scene in scenes:
            start_sample = int(
                scene.start_seconds * sample_rate
            )

            end_sample = int(
                scene.end_seconds * sample_rate
            )

            scene_audio = audio[start_sample:end_sample]

            if scene_audio.size == 0:
                average_rms = 0.0
                maximum_rms = 0.0
            else:
                average_rms = self._calculate_rms(
                    scene_audio
                )

                maximum_rms = self._calculate_peak_rms(
                    scene_audio=scene_audio,
                    sample_rate=sample_rate,
                )

            results.append(
                AudioFeatures(
                    scene_start_seconds=scene.start_seconds,
                    scene_end_seconds=scene.end_seconds,
                    average_rms=average_rms,
                    maximum_rms=maximum_rms,
                )
            )

        return results

    @staticmethod
    def _calculate_rms(
        audio: np.ndarray,
    ) -> float:
        return float(
            np.sqrt(
                np.mean(
                    np.square(audio, dtype=np.float64)
                )
            )
        )

    @staticmethod
    def _calculate_peak_rms(
        scene_audio: np.ndarray,
        sample_rate: int,
    ) -> float:
        window_size = max(
            1,
            int(sample_rate * 0.25),
        )

        peak_rms = 0.0

        for start in range(
            0,
            len(scene_audio),
            window_size,
        ):
            window = scene_audio[
                start:start + window_size
            ]

            if window.size == 0:
                continue

            rms = AudioAnalyzer._calculate_rms(window)

            peak_rms = max(
                peak_rms,
                rms,
            )

        return peak_rms