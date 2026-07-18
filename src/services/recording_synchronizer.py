# src/services/recording_synchronizer.py

from __future__ import annotations

import logging
import math
from pathlib import Path
import subprocess
import wave

import numpy as np

from src.models.recording_session import RecordingSession
from src.models.recording_synchronization import RecordingSynchronization


class RecordingSynchronizationError(RuntimeError):
    """Raised when recordings cannot be synchronized reliably."""


class RecordingSynchronizer:
    """Synchronize gameplay and facecam recordings to a master recording."""

    AUDIO_SAMPLE_RATE = 8000
    ENVELOPE_RATE = 100
    ANALYSIS_DURATION_SECONDS = 1200
    MAXIMUM_OFFSET_SECONDS = 120.0
    MINIMUM_CONFIDENCE = 0.20
    MINIMUM_PEAK_RATIO = 1.05

    def __init__(self) -> None:
        self.logger = logging.getLogger("PressStartAI")

    def synchronize(
        self,
        recording_session: RecordingSession,
        working_folder: str,
    ) -> RecordingSynchronization:
        """Calculate source offsets relative to the combined recording."""

        self._validate_session(recording_session)

        synchronization_folder = (
            Path(working_folder) / "synchronization"
        )
        synchronization_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        master_audio = synchronization_folder / "master.wav"
        gameplay_audio = synchronization_folder / "gameplay.wav"

        self._extract_audio(
            video_file=recording_session.recording_video,
            output_file=master_audio,
        )
        self._extract_audio(
            video_file=recording_session.gameplay_video or "",
            output_file=gameplay_audio,
        )
        master_envelope = self._load_envelope(master_audio)
        gameplay_envelope = self._load_envelope(gameplay_audio)
        gameplay_offset, gameplay_confidence = self._calculate_offset(
            master=master_envelope,
            source=gameplay_envelope,
            source_name="Gameplay",
        )
        synchronization = RecordingSynchronization(
            gameplay_offset_seconds=gameplay_offset,
            facecam_offset_seconds=gameplay_offset,
            gameplay_confidence=gameplay_confidence,
            facecam_confidence=gameplay_confidence,
        )

        self.logger.info("Combined Recording : Master Timeline")
        self.logger.info(
            "Gameplay Offset    : %+.3f s",
            synchronization.gameplay_offset_seconds,
        )
        self.logger.info(
            "Facecam Offset     : %+.3f s (shared OBS time base)",
            synchronization.facecam_offset_seconds,
        )
        self.logger.info(
            "Synchronization    : Successful "
            "(gameplay %.3f, facecam uses shared OBS time base)",
            synchronization.gameplay_confidence,
        )

        return synchronization

    def _validate_session(
        self,
        recording_session: RecordingSession,
    ) -> None:
        if not recording_session.has_facecam_layout:
            raise RecordingSynchronizationError(
                "Facecam Mode requires combined, gameplay, "
                "and facecam recordings."
            )

        files = {
            "Combined recording": recording_session.recording_video,
            "Gameplay recording": recording_session.gameplay_video,
            "Facecam recording": recording_session.facecam_video,
        }

        for display_name, file_name in files.items():
            path = Path(file_name or "")

            if not path.is_file():
                raise RecordingSynchronizationError(
                    f"{display_name} does not exist: {path}"
                )

    def _extract_audio(
        self,
        video_file: str,
        output_file: Path,
    ) -> None:
        command = [
            "ffmpeg",
            "-y",
            "-i",
            video_file,
            "-t",
            str(self.ANALYSIS_DURATION_SECONDS),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(self.AUDIO_SAMPLE_RATE),
            "-c:a",
            "pcm_s16le",
            str(output_file),
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode != 0:
            raise RecordingSynchronizationError(
                "Unable to extract synchronization audio from "
                f"{video_file}:\n{process.stderr}"
            )

        if not output_file.is_file():
            raise RecordingSynchronizationError(
                "Synchronization audio was not created: "
                f"{output_file}"
            )

    def _load_envelope(
        self,
        audio_file: Path,
    ) -> np.ndarray:
        samples_per_window = max(
            1,
            self.AUDIO_SAMPLE_RATE // self.ENVELOPE_RATE,
        )

        with wave.open(str(audio_file), "rb") as audio:
            sample_rate = audio.getframerate()
            channel_count = audio.getnchannels()
            sample_width = audio.getsampwidth()

            if sample_rate != self.AUDIO_SAMPLE_RATE:
                raise RecordingSynchronizationError(
                    f"Unexpected audio sample rate in {audio_file}: "
                    f"{sample_rate}"
                )

            if channel_count != 1 or sample_width != 2:
                raise RecordingSynchronizationError(
                    f"Unexpected synchronization audio format: "
                    f"{audio_file}"
                )

            raw_audio = audio.readframes(audio.getnframes())

        samples = np.frombuffer(
            raw_audio,
            dtype=np.int16,
        ).astype(np.float32)

        complete_windows = len(samples) // samples_per_window

        if complete_windows < self.ENVELOPE_RATE * 5:
            raise RecordingSynchronizationError(
                f"Recording contains insufficient audio for "
                f"synchronization: {audio_file}"
            )

        samples = samples[
            :complete_windows * samples_per_window
        ]

        windows = samples.reshape(
            complete_windows,
            samples_per_window,
        )

        envelope = np.sqrt(
            np.mean(
                np.square(windows, dtype=np.float64),
                axis=1,
            )
        )

        envelope = np.log1p(envelope)
        envelope = self._robust_normalize(envelope)

        if float(np.std(envelope)) < 0.01:
            raise RecordingSynchronizationError(
                f"Recording audio is too quiet or constant for "
                f"synchronization: {audio_file}"
            )

        return envelope.astype(np.float32)

    @staticmethod
    def _robust_normalize(
        values: np.ndarray,
    ) -> np.ndarray:
        median = float(np.median(values))
        absolute_deviation = np.abs(values - median)
        median_deviation = float(
            np.median(absolute_deviation)
        )

        scale = max(
            median_deviation * 1.4826,
            1e-6,
        )

        normalized = (values - median) / scale

        return np.clip(
            normalized,
            -8.0,
            8.0,
        )

    def _calculate_offset(
        self,
        master: np.ndarray,
        source: np.ndarray,
        source_name: str,
    ) -> tuple[float, float]:
        correlation = self._fft_correlate(
            source,
            master,
        )

        lags = np.arange(
            -(len(master) - 1),
            len(source),
            dtype=np.int64,
        )

        maximum_lag = int(
            self.MAXIMUM_OFFSET_SECONDS
            * self.ENVELOPE_RATE
        )

        valid = np.abs(lags) <= maximum_lag
        valid_correlation = correlation[valid]
        valid_lags = lags[valid]

        overlap_counts = np.minimum(
            len(source),
            len(master),
        ) - np.abs(valid_lags)

        overlap_counts = np.maximum(
            overlap_counts,
            1,
        )

        normalized_correlation = (
            valid_correlation / overlap_counts
        )

        best_index = int(
            np.argmax(normalized_correlation)
        )
        best_lag = int(valid_lags[best_index])

        coefficient = self._correlation_coefficient(
            master=master,
            source=source,
            lag=best_lag,
        )

        exclusion_radius = self.ENVELOPE_RATE
        competitor_values = normalized_correlation.copy()

        lower = max(
            0,
            best_index - exclusion_radius,
        )
        upper = min(
            len(competitor_values),
            best_index + exclusion_radius + 1,
        )

        competitor_values[lower:upper] = -np.inf
        second_peak = float(
            np.max(competitor_values)
        )

        best_peak = float(
            normalized_correlation[best_index]
        )

        if not math.isfinite(second_peak) or second_peak <= 0:
            peak_ratio = 2.0
        else:
            peak_ratio = best_peak / second_peak

        prominence_score = min(
            1.0,
            max(
                0.0,
                (peak_ratio - 1.0) / 0.25,
            ),
        )

        confidence = max(
            0.0,
            min(
                1.0,
                coefficient * 0.80
                + prominence_score * 0.20,
            ),
        )

        if (
            coefficient < self.MINIMUM_CONFIDENCE
            or peak_ratio < self.MINIMUM_PEAK_RATIO
        ):
            raise RecordingSynchronizationError(
                f"{source_name} synchronization confidence is too low. "
                f"Correlation={coefficient:.3f}, "
                f"peak ratio={peak_ratio:.3f}. "
                "Processing was stopped to prevent misaligned output."
            )

        return (
            best_lag / self.ENVELOPE_RATE,
            confidence,
        )

    @staticmethod
    def _fft_correlate(
        first: np.ndarray,
        second: np.ndarray,
    ) -> np.ndarray:
        output_length = len(first) + len(second) - 1
        fft_length = 1 << (
            output_length - 1
        ).bit_length()

        first_fft = np.fft.rfft(
            first,
            fft_length,
        )
        second_fft = np.fft.rfft(
            second[::-1],
            fft_length,
        )

        correlation = np.fft.irfft(
            first_fft * second_fft,
            fft_length,
        )

        return correlation[:output_length]

    @staticmethod
    def _correlation_coefficient(
        master: np.ndarray,
        source: np.ndarray,
        lag: int,
    ) -> float:
        if lag >= 0:
            source_start = lag
            master_start = 0
        else:
            source_start = 0
            master_start = -lag

        overlap_length = min(
            len(source) - source_start,
            len(master) - master_start,
        )

        if overlap_length <= 0:
            return 0.0

        source_slice = source[
            source_start:source_start + overlap_length
        ]
        master_slice = master[
            master_start:master_start + overlap_length
        ]

        source_centered = (
            source_slice - np.mean(source_slice)
        )
        master_centered = (
            master_slice - np.mean(master_slice)
        )

        denominator = float(
            np.linalg.norm(source_centered)
            * np.linalg.norm(master_centered)
        )

        if denominator <= 0:
            return 0.0

        coefficient = float(
            np.dot(
                source_centered,
                master_centered,
            )
            / denominator
        )

        return max(
            0.0,
            min(
                1.0,
                coefficient,
            ),
        )
