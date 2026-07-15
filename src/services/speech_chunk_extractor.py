from pathlib import Path
from typing import Any

import soundfile as sf

from src.models.speech_chunk import SpeechChunk


class SpeechChunkExtractor:
    """Merge nearby speech regions and export them as WAV files."""

    def extract(
        self,
        input_audio: str,
        speech_segments: list[dict[str, Any]],
        output_folder: str,
        merge_gap_seconds: float = 2.0,
        maximum_chunk_seconds: float = 20.0,
    ) -> list[SpeechChunk]:
        audio, sample_rate = sf.read(
            input_audio,
            dtype="float32",
            always_2d=False,
        )

        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        for old_file in output_path.glob("speech_*.wav"):
            old_file.unlink()

        merged_segments = self._merge_segments(
            speech_segments=speech_segments,
            sample_rate=sample_rate,
            merge_gap_seconds=merge_gap_seconds,
            maximum_chunk_seconds=maximum_chunk_seconds,
        )

        generated_chunks: list[SpeechChunk] = []

        for index, segment in enumerate(merged_segments, start=1):
            start_sample = int(segment["start"])
            end_sample = int(segment["end"])

            clip = audio[start_sample:end_sample]

            filename = output_path / f"speech_{index:03d}.wav"

            sf.write(
                filename,
                clip,
                sample_rate,
                subtype="PCM_16",
            )

            generated_chunks.append(
                SpeechChunk(
                    file_path=str(filename),
                    start_seconds=start_sample / sample_rate,
                    end_seconds=end_sample / sample_rate,
                )
            )

        return generated_chunks

    @staticmethod
    def _merge_segments(
        speech_segments: list[dict[str, Any]],
        sample_rate: int,
        merge_gap_seconds: float,
        maximum_chunk_seconds: float,
    ) -> list[dict[str, int]]:
        if not speech_segments:
            return []

        merge_gap_samples = int(merge_gap_seconds * sample_rate)
        maximum_chunk_samples = int(maximum_chunk_seconds * sample_rate)

        merged: list[dict[str, int]] = []

        current_start = int(speech_segments[0]["start"])
        current_end = int(speech_segments[0]["end"])

        for segment in speech_segments[1:]:
            next_start = int(segment["start"])
            next_end = int(segment["end"])

            gap = next_start - current_end
            proposed_duration = next_end - current_start

            should_merge = (
                gap <= merge_gap_samples
                and proposed_duration <= maximum_chunk_samples
            )

            if should_merge:
                current_end = next_end
                continue

            merged.append(
                {
                    "start": current_start,
                    "end": current_end,
                }
            )

            current_start = next_start
            current_end = next_end

        merged.append(
            {
                "start": current_start,
                "end": current_end,
            }
        )

        return merged