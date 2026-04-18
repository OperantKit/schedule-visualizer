"""Tests for the ``timeline`` data structures."""

from __future__ import annotations

import dataclasses

import pytest

from schedule_visualizer.timeline import (
    EVENT_RF_AVAILABLE,
    EVENT_SD_ON,
    KNOWN_EVENT_TYPES,
    ScheduleTimeline,
    TimelineEvent,
)


@pytest.mark.unit
def test_timeline_event_is_frozen() -> None:
    ev = TimelineEvent(timestamp=1.0, event_type=EVENT_RF_AVAILABLE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.timestamp = 2.0  # type: ignore[misc]


@pytest.mark.unit
def test_timeline_event_orderable_by_timestamp() -> None:
    a = TimelineEvent(timestamp=1.0, event_type=EVENT_SD_ON)
    b = TimelineEvent(timestamp=2.0, event_type=EVENT_SD_ON)
    c = TimelineEvent(timestamp=2.0, event_type=EVENT_RF_AVAILABLE)
    assert a < b
    assert sorted([b, a, c]) == [a, c, b]  # rf_available < sd_on alphabetically


@pytest.mark.unit
def test_known_event_types_constant_is_frozenset() -> None:
    assert isinstance(KNOWN_EVENT_TYPES, frozenset)
    assert EVENT_RF_AVAILABLE in KNOWN_EVENT_TYPES
    assert EVENT_SD_ON in KNOWN_EVENT_TYPES


@pytest.mark.unit
def test_schedule_timeline_add_and_events_returns_sorted() -> None:
    tl = ScheduleTimeline(duration_s=10.0)
    tl.add_event(TimelineEvent(timestamp=5.0, event_type=EVENT_RF_AVAILABLE))
    tl.add_event(TimelineEvent(timestamp=1.0, event_type=EVENT_RF_AVAILABLE))
    tl.add_event(TimelineEvent(timestamp=3.0, event_type=EVENT_RF_AVAILABLE))

    events = tl.events()
    assert [e.timestamp for e in events] == [1.0, 3.0, 5.0]


@pytest.mark.unit
def test_schedule_timeline_events_returns_fresh_list() -> None:
    tl = ScheduleTimeline(duration_s=10.0)
    tl.add_event(TimelineEvent(timestamp=1.0, event_type=EVENT_RF_AVAILABLE))
    first = tl.events()
    first.clear()
    assert len(tl.events()) == 1, "events() must return a defensive copy"


@pytest.mark.unit
def test_schedule_timeline_components_default_single_lane() -> None:
    tl = ScheduleTimeline(duration_s=10.0, schedule_str="FI 5s")
    tl.add_event(TimelineEvent(timestamp=5.0, event_type=EVENT_RF_AVAILABLE))
    assert tl.components() == [""]


@pytest.mark.unit
def test_schedule_timeline_components_preserves_first_seen_order() -> None:
    tl = ScheduleTimeline(duration_s=10.0)
    tl.add_event(
        TimelineEvent(timestamp=1.0, event_type=EVENT_RF_AVAILABLE, component="comp1")
    )
    tl.add_event(
        TimelineEvent(timestamp=2.0, event_type=EVENT_RF_AVAILABLE, component="comp2")
    )
    tl.add_event(
        TimelineEvent(timestamp=3.0, event_type=EVENT_RF_AVAILABLE, component="comp1")
    )
    assert tl.components() == ["comp1", "comp2"]


@pytest.mark.unit
def test_schedule_timeline_empty_components() -> None:
    tl = ScheduleTimeline(duration_s=10.0)
    assert tl.components() == []
    assert tl.events() == []
