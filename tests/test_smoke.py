"""Smoke tests covering the public surface of schedule_visualizer."""

from __future__ import annotations

import schedule_visualizer


def test_public_api_exports() -> None:
    expected = {
        "ScheduleParseError",
        "ScheduleTimeline",
        "TimelineEvent",
        "render_timeline",
        "step_schedule",
    }
    assert expected.issubset(set(schedule_visualizer.__all__))
    for name in expected:
        assert hasattr(schedule_visualizer, name), f"missing public export: {name}"
