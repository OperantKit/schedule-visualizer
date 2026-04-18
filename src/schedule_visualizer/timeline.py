"""Timeline data structures.

A ``ScheduleTimeline`` collects ``TimelineEvent`` records describing things
that the schedule causes to happen at specific points in time (or, for
ratio-style schedules, things that are *response-dependent* and therefore
attached as annotations rather than placed on the time axis).

This module is deliberately backend-agnostic: it knows nothing about
matplotlib, plotting, or the schedule grammar. ``stepper`` populates it,
``render`` consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

# Canonical event-type strings recognised by the renderer.
EVENT_SD_ON: Final[str] = "sd_on"
EVENT_SD_OFF: Final[str] = "sd_off"
EVENT_RF_AVAILABLE: Final[str] = "rf_available"
EVENT_RF_CONSUMED: Final[str] = "rf_consumed"
EVENT_RF_AFTER_RESPONSE: Final[str] = "rf_after_response_n"
EVENT_NO_RF: Final[str] = "no_rf"

KNOWN_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        EVENT_SD_ON,
        EVENT_SD_OFF,
        EVENT_RF_AVAILABLE,
        EVENT_RF_CONSUMED,
        EVENT_RF_AFTER_RESPONSE,
        EVENT_NO_RF,
    }
)


@dataclass(frozen=True, order=True)
class TimelineEvent:
    """A single scheduled event on the timeline.

    Ordering is by ``timestamp`` first then ``event_type`` so that lists of
    events are deterministically sortable (useful for snapshot tests).

    ``timestamp`` is in seconds. For response-dependent annotations the
    canonical convention is to set ``timestamp = 0.0`` and put the
    ratio/response count in ``label``.
    """

    timestamp: float
    event_type: str
    label: str | None = None
    component: str | None = None


@dataclass
class ScheduleTimeline:
    """A collection of ``TimelineEvent`` objects sharing a duration window.

    ``time_step_s`` is informational (used by the renderer to choose tick
    spacing). The stepper does not actually discretise anything to a grid;
    events are placed at their natural floating-point timestamps.
    """

    duration_s: float
    time_step_s: float = 0.1
    schedule_str: str = ""
    _events: list[TimelineEvent] = field(default_factory=list)

    def add_event(self, event: TimelineEvent) -> None:
        """Append a single event. Order is preserved by ``events()``."""

        self._events.append(event)

    def events(self) -> list[TimelineEvent]:
        """Return events sorted by ``(timestamp, event_type)``.

        The returned list is a fresh copy, so callers may mutate it freely
        without disturbing internal state.
        """

        return sorted(self._events)

    def components(self) -> list[str]:
        """Return the distinct component labels present in the timeline.

        For atomic schedules the result is ``[""]`` (no component grouping).
        For compound schedules each lane shows up once, in first-seen order.
        """

        seen: list[str] = []
        for ev in self._events:
            key = ev.component or ""
            if key not in seen:
                seen.append(key)
        return seen
