"""Schedule stepper: parse a schedule string into a ``ScheduleTimeline``.

Scope
-----
This module implements **only** the dry-run availability semantics described
in the package docstring. It walks the time axis from ``0`` to
``duration_s`` and emits ``rf_available`` events at the times reinforcement
would become available under each supported schedule.

Supported syntax (case-insensitive for the family name):

    Atomic (time-domain, units accepted: ``s``/``ms``/``min``):
        FI t   - fixed interval, RF available at t, 2t, 3t, ...
        VI t   - variable interval (mean t), times sampled with seed
        RI t   - random interval (mean t), Bernoulli at each second tick
        FT t   - fixed time, same as FI for availability purposes
        VT t   - variable time, same emission as VI
        RT t   - random time, same emission as RI

    Atomic (ratio-domain, response-dependent — annotated, not placed):
        FR n   - fixed ratio, annotated as rf_after_response_n=n
        VR n   - variable ratio (mean n), annotated as response-dependent
        RR n   - random ratio (mean n), annotated as response-dependent
        CRF    - continuous reinforcement, annotated as response-dependent
        EXT    - extinction, no events emitted

    Compound:
        Conc(s1, s2, ...)   - concurrent
        Mult(s1, s2, ...)   - multiple
        Chain(s1, s2, ...)  - chained

The parser is intentionally local (no dependency on ``contingency-py`` or
``contingency-dsl``); the supported subset is small enough that a hand-rolled
recursive splitter handles it cleanly.

Headless safety: the matplotlib ``Agg`` backend is selected at import time so
that callers running on CI / headless servers do not need to set
``MPLBACKEND`` themselves.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

import matplotlib

# Force a non-interactive backend before any pyplot import elsewhere in the
# process. This makes the package safe to import on headless CI runners.
matplotlib.use("Agg", force=False)

from schedule_visualizer.timeline import (
    EVENT_NO_RF,
    EVENT_RF_AFTER_RESPONSE,
    EVENT_RF_AVAILABLE,
    ScheduleTimeline,
    TimelineEvent,
)


class ScheduleParseError(ValueError):
    """Raised for schedule strings outside the supported subset."""


# ---------------------------------------------------------------------------
# AST
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Atomic:
    family: str  # upper-case: FR, VR, RR, FI, VI, RI, FT, VT, RT, CRF, EXT
    parameter: float | None  # None for CRF/EXT, ratio count for FR/VR/RR (int-valued)
    raw: str


@dataclass(frozen=True)
class _Compound:
    combinator: str  # upper-case: CONC, MULT, CHAIN
    children: tuple[_Atomic | _Compound, ...]
    raw: str


_Node = _Atomic | _Compound


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_TIME_DOMAIN_FAMILIES = frozenset({"FI", "VI", "RI", "FT", "VT", "RT"})
_RATIO_DOMAIN_FAMILIES = frozenset({"FR", "VR", "RR"})
_PARAMETERLESS_FAMILIES = frozenset({"CRF", "EXT"})
_ATOMIC_FAMILIES = _TIME_DOMAIN_FAMILIES | _RATIO_DOMAIN_FAMILIES | _PARAMETERLESS_FAMILIES

_COMBINATOR_ALIASES = {
    "CONC": "CONC",
    "CONCURRENT": "CONC",
    "MULT": "MULT",
    "MULTIPLE": "MULT",
    "CHAIN": "CHAIN",
    "CHAINED": "CHAIN",
}

# "FR 5", "VI 30s", "FI 1.5min", "FT 250ms"
_ATOMIC_RE = re.compile(
    r"""
    ^\s*
    (?P<family>[A-Za-z]+)        # family name
    (?:\s+
        (?P<value>[0-9]+(?:\.[0-9]+)?)
        \s*
        (?P<unit>ms|s|min)?       # optional time unit
    )?
    \s*$
    """,
    re.VERBOSE,
)


def _split_top_level(args: str) -> list[str]:
    """Split a comma-separated argument list respecting nested parentheses."""

    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in args:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ScheduleParseError(f"Unbalanced parentheses in {args!r}")
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if depth != 0:
        raise ScheduleParseError(f"Unbalanced parentheses in {args!r}")
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse(text: str) -> _Node:
    raw = text.strip()
    if not raw:
        raise ScheduleParseError("Empty schedule string")

    # Compound? "Name(...)"
    m = re.match(r"^\s*([A-Za-z]+)\s*\((.*)\)\s*$", raw, re.DOTALL)
    if m:
        name = m.group(1).upper()
        if name in _COMBINATOR_ALIASES:
            combinator = _COMBINATOR_ALIASES[name]
            inner_args = _split_top_level(m.group(2))
            if not inner_args:
                raise ScheduleParseError(f"{combinator} requires at least one component")
            children = tuple(_parse(arg) for arg in inner_args)
            return _Compound(combinator=combinator, children=children, raw=raw)
        # Fall through: an atomic family that happens to look like Name(...)
        # is not supported.
        raise ScheduleParseError(f"Unknown combinator: {name!r}")

    # Atomic
    am = _ATOMIC_RE.match(raw)
    if not am:
        raise ScheduleParseError(f"Could not parse schedule: {raw!r}")

    family = am.group("family").upper()
    value_s = am.group("value")
    unit = am.group("unit")

    if family not in _ATOMIC_FAMILIES:
        raise ScheduleParseError(f"Unknown schedule family: {family!r}")

    if family in _PARAMETERLESS_FAMILIES:
        if value_s is not None:
            raise ScheduleParseError(f"{family} takes no parameter, got {value_s!r}")
        return _Atomic(family=family, parameter=None, raw=raw)

    if value_s is None:
        raise ScheduleParseError(f"{family} requires a numeric parameter")

    value = float(value_s)

    if family in _TIME_DOMAIN_FAMILIES:
        if unit == "ms":
            value /= 1000.0
        elif unit == "min":
            value *= 60.0
        # default "s" or no unit → already in seconds
    elif family in _RATIO_DOMAIN_FAMILIES:
        if unit is not None:
            raise ScheduleParseError(
                f"{family} is a ratio schedule and does not take a time unit ({unit!r})"
            )
        if value <= 0:
            raise ScheduleParseError(f"{family} parameter must be positive, got {value}")
        # The ratio value is a response count (RR n is a mean ratio with
        # per-response probability 1/n, not the probability itself), so a
        # fractional value is rejected rather than truncated by int().
        if not value.is_integer():
            raise ScheduleParseError(
                f"{family} parameter must be an integer response count, got {value_s}"
            )

    return _Atomic(family=family, parameter=value, raw=raw)


# ---------------------------------------------------------------------------
# Stepping
# ---------------------------------------------------------------------------


def _component_label(node: _Node, index: int) -> str:
    """Compact label used for compound-schedule lanes ("comp1: FI 30s")."""

    return f"comp{index + 1}: {node.raw.strip()}"


def _step_atomic(
    node: _Atomic,
    timeline: ScheduleTimeline,
    component: str,
    rng: random.Random,
) -> None:
    family = node.family
    duration = timeline.duration_s

    if family == "EXT":
        timeline.add_event(
            TimelineEvent(
                timestamp=0.0,
                event_type=EVENT_NO_RF,
                label="EXT (extinction): no reinforcement",
                component=component,
            )
        )
        return

    if family == "CRF":
        timeline.add_event(
            TimelineEvent(
                timestamp=0.0,
                event_type=EVENT_RF_AFTER_RESPONSE,
                label="CRF: rf_after_response_n=1 (response-dependent)",
                component=component,
            )
        )
        return

    if family in _RATIO_DOMAIN_FAMILIES:
        assert node.parameter is not None
        n = node.parameter
        if family == "FR":
            label = f"FR {int(n)}: rf_after_response_n={int(n)} (response-dependent)"
        elif family == "VR":
            label = f"VR {int(n)}: rf_after_response_n~mean={int(n)} (response-dependent)"
        else:  # RR
            label = (
                f"RR {int(n)}: rf_after_response_n~Bernoulli(1/{int(n)}) "
                "(response-dependent)"
            )
        timeline.add_event(
            TimelineEvent(
                timestamp=0.0,
                event_type=EVENT_RF_AFTER_RESPONSE,
                label=label,
                component=component,
            )
        )
        return

    # Time-domain families
    assert node.parameter is not None
    interval = node.parameter
    if interval <= 0:
        raise ScheduleParseError(f"{family} parameter must be positive, got {interval}")

    if family in {"FI", "FT"}:
        t = interval
        while t <= duration + 1e-9:
            timeline.add_event(
                TimelineEvent(
                    timestamp=t,
                    event_type=EVENT_RF_AVAILABLE,
                    label=f"{family} {interval}s",
                    component=component,
                )
            )
            t += interval
        return

    if family in {"VI", "VT"}:
        # Variable interval: sample successive intervals from an exponential
        # distribution with the given mean (memoryless approximation; for
        # dry-run visualization purposes Fleshler-Hoffman would also be valid
        # but the seed-driven exponential is faithful enough and trivially
        # deterministic).
        t = 0.0
        while True:
            delta = rng.expovariate(1.0 / interval)
            t += delta
            if t > duration + 1e-9:
                return
            timeline.add_event(
                TimelineEvent(
                    timestamp=t,
                    event_type=EVENT_RF_AVAILABLE,
                    label=f"{family} mean={interval}s",
                    component=component,
                )
            )

    if family in {"RI", "RT"}:
        # Random interval: at each integer-second tick, RF becomes available
        # with probability 1/mean. (For sub-second means we still tick at 1s
        # but cap probability at 1.0.)
        p = min(1.0, 1.0 / interval)
        t = 1.0
        while t <= duration + 1e-9:
            if rng.random() < p:
                timeline.add_event(
                    TimelineEvent(
                        timestamp=t,
                        event_type=EVENT_RF_AVAILABLE,
                        label=f"{family} mean={interval}s",
                        component=component,
                    )
                )
            t += 1.0


def _step_node(
    node: _Node,
    timeline: ScheduleTimeline,
    component: str,
    rng: random.Random,
) -> None:
    if isinstance(node, _Atomic):
        _step_atomic(node, timeline, component, rng)
        return

    # Compound: each child gets its own component lane.
    for idx, child in enumerate(node.children):
        child_label = _component_label(child, idx)
        if component:
            child_label = f"{component} / {child_label}"
        _step_node(child, timeline, child_label, rng)


def step_schedule(
    schedule_str: str,
    duration_s: float,
    time_step_s: float = 0.1,
    seed: int | None = None,
) -> ScheduleTimeline:
    """Parse ``schedule_str`` and produce a dry-run availability timeline.

    Parameters
    ----------
    schedule_str
        Schedule expression in the supported subset (see module docstring).
    duration_s
        Length of the dry-run window, in seconds. Must be positive.
    time_step_s
        Tick spacing for the renderer (informational; the stepper itself
        emits events at their natural floating-point timestamps).
    seed
        RNG seed for stochastic schedules (VI/VT, RI/RT, VR/RR). When
        ``None``, a fresh non-deterministic RNG is used. Pin the seed in
        tests for reproducibility.

    Returns
    -------
    ScheduleTimeline
        Sorted by ``(timestamp, event_type)`` via ``events()``.

    Notes
    -----
    Ratio schedules (FR/VR/RR/CRF) are response-dependent. Because the
    visualizer is dry-run only — there is no virtual subject — these are
    rendered as annotations at ``t=0`` with an ``rf_after_response_n``
    label, *not* as time-located ``rf_available`` markers. Use the sibling
    ``behavior-simulator`` package for response-conditional simulations.
    """

    if duration_s <= 0:
        raise ValueError(f"duration_s must be positive, got {duration_s}")
    if time_step_s <= 0:
        raise ValueError(f"time_step_s must be positive, got {time_step_s}")

    node = _parse(schedule_str)
    timeline = ScheduleTimeline(
        duration_s=duration_s,
        time_step_s=time_step_s,
        schedule_str=schedule_str,
    )
    rng = random.Random(seed)
    _step_node(node, timeline, component="", rng=rng)
    return timeline
