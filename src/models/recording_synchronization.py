# src/models/recording_synchronization.py

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RecordingSynchronization:
    """Time offsets that map the master timeline to source recordings.

    Source timestamp = master timestamp + source offset.
    """

    gameplay_offset_seconds: float
    facecam_offset_seconds: float
    gameplay_confidence: float
    facecam_confidence: float

    @property
    def minimum_confidence(self) -> float:
        """Return the lower synchronization confidence."""

        return min(
            self.gameplay_confidence,
            self.facecam_confidence,
        )
