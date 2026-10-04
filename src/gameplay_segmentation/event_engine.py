from __future__ import annotations

from typing import List
from .models import Event, EventState

class TemporalEventEngine:
    """
    Sole authority for gameplay event generation.
    """

    def propose(self, scenes) -> List[Event]:
        events = []

        for scene in scenes:
            events.append(
                Event.create(
                    start=scene.start,
                    end=scene.end,
                    category="Gameplay",
                    description=scene.transcript or "Gameplay event",
                    confidence=scene.score,
                )
            )

        return events

    def apply_ai(self, events, ai_results):
        lookup = {x["event_id"]: x for x in ai_results}

        for event in events:
            ai = lookup.get(event.event_id)

            if ai is None:
                event.state = EventState.AI_FAILED
                continue

            if ai["meaningful"]:
                event.state = EventState.AI_CONFIRMED
                event.description = ai["description"]
            else:
                event.state = EventState.AI_REJECTED

        return events

    def refine_boundaries(self, events):
        for event in events:
            if event.state == EventState.AI_CONFIRMED:
                event.state = EventState.BOUNDARY_REFINED
        return events

    def deduplicate(self, events):
        accepted = []

        for event in events:
            if event.state in (
                EventState.BOUNDARY_REFINED,
                EventState.AI_UNCERTAIN,
            ):
                event.state = EventState.DEDUPED
                accepted.append(event)

        return accepted