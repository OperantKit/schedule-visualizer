"""Render a ``ScheduleTimeline`` to a PNG file.

The renderer uses matplotlib's non-interactive ``Agg`` backend (selected at
import time in ``stepper``) so it works on headless CI runners without an
``$DISPLAY``. The output is a horizontal lane chart: one lane per component
of the (possibly compound) schedule, time on the x-axis, and color-coded
markers for each event type.

Response-dependent annotations (FR/VR/RR/CRF) are placed at ``t = 0`` as text
labels rather than markers, so they do not pretend to occupy real time.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
from matplotlib.artist import Artist

matplotlib.use("Agg", force=False)

import matplotlib.pyplot as plt

from schedule_visualizer.timeline import (
    EVENT_NO_RF,
    EVENT_RF_AFTER_RESPONSE,
    EVENT_RF_AVAILABLE,
    EVENT_RF_CONSUMED,
    EVENT_SD_OFF,
    EVENT_SD_ON,
    ScheduleTimeline,
)

_EVENT_STYLE: dict[str, tuple[str, str]] = {
    # event_type -> (matplotlib marker, color)
    EVENT_RF_AVAILABLE: ("o", "tab:green"),
    EVENT_RF_CONSUMED: ("X", "tab:olive"),
    EVENT_RF_AFTER_RESPONSE: ("D", "tab:purple"),
    EVENT_SD_ON: ("^", "tab:blue"),
    EVENT_SD_OFF: ("v", "tab:gray"),
    EVENT_NO_RF: ("s", "tab:red"),
}

_DEFAULT_STYLE: tuple[str, str] = (".", "tab:orange")


def render_timeline(
    timeline: ScheduleTimeline,
    output_path: str | Path,
) -> Path:
    """Render ``timeline`` to a PNG at ``output_path`` and return the path.

    The output directory must already exist. The function returns the
    resolved ``Path`` of the file it wrote so callers can chain it into
    further processing.
    """

    out = Path(output_path)
    if out.parent and not out.parent.exists():
        raise FileNotFoundError(f"Output directory does not exist: {out.parent}")

    components = timeline.components() or [""]
    n_lanes = len(components)
    fig_height = max(2.0, 0.6 + 0.7 * n_lanes)
    fig, ax = plt.subplots(figsize=(10.0, fig_height))

    # Draw a horizontal guide line for each lane.
    for lane_idx, comp in enumerate(components):
        ax.hlines(
            y=lane_idx,
            xmin=0.0,
            xmax=timeline.duration_s,
            colors="lightgray",
            linewidth=1.0,
            zorder=1,
        )
        # Lane label on the left.
        label = comp if comp else (timeline.schedule_str or "schedule")
        ax.text(
            -0.01 * max(timeline.duration_s, 1.0),
            lane_idx,
            label,
            ha="right",
            va="center",
            fontsize=8,
        )

    lane_for: dict[str, int] = {comp: idx for idx, comp in enumerate(components)}

    # Plot events. Track which event_types we actually drew so the legend is
    # not polluted with unused entries.
    drawn_types: set[str] = set()
    for ev in timeline.events():
        marker, color = _EVENT_STYLE.get(ev.event_type, _DEFAULT_STYLE)
        lane = lane_for.get(ev.component or "", 0)
        ax.scatter(
            [ev.timestamp],
            [lane],
            marker=marker,
            color=color,
            s=70,
            zorder=3,
            label=ev.event_type if ev.event_type not in drawn_types else None,
        )
        drawn_types.add(ev.event_type)
        # Annotate response-dependent / no-RF labels inline so the figure is
        # interpretable without reading the underlying timeline object.
        if ev.event_type in {EVENT_RF_AFTER_RESPONSE, EVENT_NO_RF} and ev.label:
            ax.text(
                ev.timestamp + 0.02 * max(timeline.duration_s, 1.0),
                lane + 0.18,
                ev.label,
                fontsize=7,
                color=color,
                va="bottom",
            )

    ax.set_xlim(-0.05 * max(timeline.duration_s, 1.0), timeline.duration_s * 1.05)
    ax.set_ylim(-0.6, max(0.6, n_lanes - 0.4))
    ax.set_yticks([])
    ax.set_xlabel("Time (s)")
    title = timeline.schedule_str or "schedule"
    ax.set_title(f"Dry-run schedule timeline: {title}  (duration {timeline.duration_s:g}s)")
    ax.grid(axis="x", linestyle=":", alpha=0.4)

    if drawn_types:
        # De-duplicate legend entries (the loop above already filters by
        # passing label=None on repeats, but matplotlib still keeps order).
        handles, labels = ax.get_legend_handles_labels()
        seen: dict[str, Artist] = {}
        for h, lbl in zip(handles, labels, strict=False):
            if lbl not in seen:
                seen[lbl] = h
        ax.legend(
            list(seen.values()),
            list(seen.keys()),
            loc="upper right",
            fontsize=8,
            framealpha=0.9,
        )

    fig.tight_layout()
    fig.savefig(out, dpi=120, format="png")
    plt.close(fig)
    return out
