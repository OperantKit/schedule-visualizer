"""schedule-visualizer: dry-run timeline visualizer for reinforcement schedules.

Public surface
--------------
``ScheduleTimeline``, ``TimelineEvent``
    Data structures describing scheduled events on a timeline.
``step_schedule``
    Parse a schedule string and produce a ``ScheduleTimeline`` of when
    reinforcement would become available over a given duration.
``render_timeline``
    Render a ``ScheduleTimeline`` to a PNG file using matplotlib.
``ScheduleParseError``
    Raised for schedule strings that fall outside the supported subset.
"""

from __future__ import annotations

from schedule_visualizer.render import render_timeline
from schedule_visualizer.stepper import ScheduleParseError, step_schedule
from schedule_visualizer.timeline import ScheduleTimeline, TimelineEvent

__all__ = [
    "ScheduleParseError",
    "ScheduleTimeline",
    "TimelineEvent",
    "render_timeline",
    "step_schedule",
]
