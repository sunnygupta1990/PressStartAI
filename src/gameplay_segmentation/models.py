from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


# ==========================================================
# Existing timeline model (unchanged)
# ==========================================================

@dataclass(slots=True, frozen=True)
class TimelineObservation:
    timestamp: float
    motion_score: float
    visual_change_score: float
    brightness: float
    speech_active: bool = False


# ==========================================================
# Event lifecycle
# ==========================================================

class EventState(str, Enum):
    PROPOSED = "PROPOSED"
    AI_CONFIRMED = "AI_CONFIRMED"
    AI_REJECTED = "AI_REJECTED"
    AI_UNCERTAIN = "AI_UNCERTAIN"
    AI_FAILED = "AI_FAILED"
    BOUNDARY_REFINED = "BOUNDARY_REFINED"
    DEDUPED = "DEDUPED"
    EXPORTED = "EXPORTED"


# ==========================================================
# Persistent entities
# ==========================================================

@dataclass(slots=True)
class CharacterEntity:
    entity_id: str
    canonical_name: str
    aliases: set[str] = field(default_factory=set)
    confidence: float = 1.0
    last_seen: float = 0.0

    @staticmethod
    def create(name: str) -> "CharacterEntity":
        return CharacterEntity(
            entity_id=f"C_{uuid4().hex[:8].upper()}",
            canonical_name=name,
        )


@dataclass(slots=True)
class LocationEntity:
    location_id: str
    canonical_name: str
    confidence: float = 1.0
    last_seen: float = 0.0

    @staticmethod
    def create(name: str) -> "LocationEntity":
        return LocationEntity(
            location_id=f"L_{uuid4().hex[:8].upper()}",
            canonical_name=name,
        )


# ==========================================================
# Canonical Event (NEW)
# ==========================================================

@dataclass(slots=True)
class Event:
    event_id: str
    state: EventState
    start: float
    end: float
    category: str
    description: str
    characters: list[str] = field(default_factory=list)
    location: str = "Unknown"
    shot_type: str = "Gameplay"
    dialogue_present: bool = False
    confidence: float = 0.0
    repetition: float = 0.0

    @staticmethod
    def create(
        *,
        start: float,
        end: float,
        category: str,
        description: str,
        characters: list[str] | None = None,
        location: str = "Unknown",
        shot_type: str = "Gameplay",
        dialogue_present: bool = False,
        confidence: float = 0.0,
    ) -> "Event":
        return Event(
            event_id=f"E_{uuid4().hex[:8].upper()}",
            state=EventState.PROPOSED,
            start=start,
            end=end,
            category=category,
            description=description,
            characters=characters or [],
            location=location,
            shot_type=shot_type,
            dialogue_present=dialogue_present,
            confidence=confidence,
        )


# ==========================================================
# Existing compatibility models
# ==========================================================

@dataclass(slots=True, frozen=True)
class EventRegion:
    start_seconds: float
    end_seconds: float
    category: str
    description: str
    characters: tuple[str, ...] = ()
    location: str = "Unknown"
    shot_type: str = "Gameplay"
    dialogue_present: bool = False
    confidence: float = 0.0
    repetition: float = 0.0
    source_window_start: float = 0.0
    source_window_end: float = 0.0


@dataclass(slots=True, frozen=True)
class ClipCandidate:
    start_seconds: float
    end_seconds: float
    category: str
    description: str
    characters: tuple[str, ...] = ()
    location: str = "Unknown"
    shot_type: str = "Gameplay"
    dialogue_present: bool = False
    confidence: float = 0.0
    source_event_index: int = -1
    reason: str = ""


# ==========================================================
# Export model
# ==========================================================

@dataclass(slots=True, frozen=True)
class ClipRecord:
    clip_id: str
    file_path: str
    relative_file_path: str
    source_video: str
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    category: str
    subcategory: str
    description: str
    characters: tuple[str, ...]
    location: str
    shot_type: str
    dialogue_present: bool
    transcript: str
    confidence: float
    source_event_index: int
    event_id: str = ""
    overlapped_clip_ids: tuple[str, ...] = ()
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "clip_id": self.clip_id,
            "event_id": self.event_id,
            "file_path": self.file_path,
            "relative_file_path": self.relative_file_path,
            "source_video": self.source_video,
            "start_seconds": round(self.start_seconds, 3),
            "end_seconds": round(self.end_seconds, 3),
            "duration_seconds": round(self.duration_seconds, 3),
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
            "action_event": self.description,
            "characters": list(self.characters),
            "location": self.location,
            "shot_type": self.shot_type,
            "dialogue_present": self.dialogue_present,
            "transcript": self.transcript,
            "confidence": round(self.confidence, 4),
            "source_event_index": self.source_event_index,
            "overlapped_clip_ids": list(self.overlapped_clip_ids),
        }