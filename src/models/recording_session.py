# src/models/recording_session.py

from dataclasses import dataclass

from src.models.recording_synchronization import RecordingSynchronization


@dataclass(slots=True)
class RecordingSession:
    """Represent the recordings and synchronization for one pipeline run."""

    recording_video: str
    gameplay_video: str | None = None
    facecam_video: str | None = None
    synchronization: RecordingSynchronization | None = None

    @property
    def has_facecam_layout(self) -> bool:
        """Return whether separate gameplay and facecam files are present."""

        return (
            self.gameplay_video is not None
            and self.facecam_video is not None
        )

    @property
    def is_synchronized(self) -> bool:
        """Return whether Facecam Mode synchronization has completed."""

        return self.synchronization is not None

    def gameplay_timestamp(
        self,
        master_timestamp_seconds: float,
    ) -> float:
        """Convert a master timestamp to the gameplay timeline."""

        if self.synchronization is None:
            raise RuntimeError(
                "Gameplay timestamp requested before synchronization."
            )

        return (
            master_timestamp_seconds
            + self.synchronization.gameplay_offset_seconds
        )

    def facecam_timestamp(
        self,
        master_timestamp_seconds: float,
    ) -> float:
        """Convert a master timestamp to the facecam timeline."""

        if self.synchronization is None:
            raise RuntimeError(
                "Facecam timestamp requested before synchronization."
            )

        return (
            master_timestamp_seconds
            + self.synchronization.facecam_offset_seconds
        )