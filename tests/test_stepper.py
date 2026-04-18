"""Tests for the schedule stepper.

These tests cover the dry-run availability semantics for each supported
schedule family as well as the compound combinators ``Conc``, ``Mult``, and
``Chain``.
"""

from __future__ import annotations

import pytest

from schedule_visualizer.stepper import ScheduleParseError, step_schedule
from schedule_visualizer.timeline import (
    EVENT_NO_RF,
    EVENT_RF_AFTER_RESPONSE,
    EVENT_RF_AVAILABLE,
)


# ---------------------------------------------------------------------------
# Time-domain schedules
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fi_emits_rf_at_each_interval() -> None:
    tl = step_schedule("FI 30s", duration_s=90.0)
    times = [e.timestamp for e in tl.events() if e.event_type == EVENT_RF_AVAILABLE]
    assert times == pytest.approx([30.0, 60.0, 90.0])


@pytest.mark.unit
def test_fi_with_minutes_unit() -> None:
    tl = step_schedule("FI 1min", duration_s=180.0)
    times = [e.timestamp for e in tl.events() if e.event_type == EVENT_RF_AVAILABLE]
    assert times == pytest.approx([60.0, 120.0, 180.0])


@pytest.mark.unit
def test_fi_with_milliseconds_unit() -> None:
    tl = step_schedule("FI 500ms", duration_s=2.0)
    times = [e.timestamp for e in tl.events() if e.event_type == EVENT_RF_AVAILABLE]
    assert times == pytest.approx([0.5, 1.0, 1.5, 2.0])


@pytest.mark.unit
def test_ft_behaves_like_fi_for_availability() -> None:
    tl = step_schedule("FT 20s", duration_s=80.0)
    times = [e.timestamp for e in tl.events() if e.event_type == EVENT_RF_AVAILABLE]
    assert times == pytest.approx([20.0, 40.0, 60.0, 80.0])


@pytest.mark.unit
def test_vi_seeded_is_deterministic() -> None:
    a = step_schedule("VI 30s", duration_s=120.0, seed=42)
    b = step_schedule("VI 30s", duration_s=120.0, seed=42)
    assert [e.timestamp for e in a.events()] == [e.timestamp for e in b.events()]


@pytest.mark.unit
def test_vi_different_seed_yields_different_events() -> None:
    a = step_schedule("VI 30s", duration_s=300.0, seed=1)
    b = step_schedule("VI 30s", duration_s=300.0, seed=2)
    assert [e.timestamp for e in a.events()] != [e.timestamp for e in b.events()]


@pytest.mark.unit
def test_vi_events_within_duration_window() -> None:
    tl = step_schedule("VI 10s", duration_s=60.0, seed=7)
    for ev in tl.events():
        assert 0.0 < ev.timestamp <= 60.0 + 1e-9


@pytest.mark.unit
def test_ri_seeded_is_deterministic() -> None:
    a = step_schedule("RI 5s", duration_s=60.0, seed=99)
    b = step_schedule("RI 5s", duration_s=60.0, seed=99)
    assert [e.timestamp for e in a.events()] == [e.timestamp for e in b.events()]


@pytest.mark.unit
def test_rt_emits_only_rf_available() -> None:
    tl = step_schedule("RT 5s", duration_s=20.0, seed=3)
    for ev in tl.events():
        assert ev.event_type == EVENT_RF_AVAILABLE


# ---------------------------------------------------------------------------
# Ratio-domain (response-dependent) schedules
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fr_annotated_as_response_dependent() -> None:
    tl = step_schedule("FR 5", duration_s=60.0)
    events = tl.events()
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == EVENT_RF_AFTER_RESPONSE
    assert ev.timestamp == 0.0
    assert "rf_after_response_n=5" in (ev.label or "")


@pytest.mark.unit
def test_fr_emits_no_rf_available_markers() -> None:
    tl = step_schedule("FR 5", duration_s=60.0)
    assert all(e.event_type != EVENT_RF_AVAILABLE for e in tl.events())


@pytest.mark.unit
def test_vr_annotated_as_response_dependent() -> None:
    tl = step_schedule("VR 10", duration_s=60.0, seed=1)
    events = tl.events()
    assert len(events) == 1
    assert events[0].event_type == EVENT_RF_AFTER_RESPONSE
    assert "VR 10" in (events[0].label or "")


@pytest.mark.unit
def test_rr_annotated_as_response_dependent() -> None:
    tl = step_schedule("RR 8", duration_s=60.0, seed=1)
    events = tl.events()
    assert len(events) == 1
    assert events[0].event_type == EVENT_RF_AFTER_RESPONSE
    assert "Bernoulli" in (events[0].label or "")


@pytest.mark.unit
def test_crf_annotated_as_response_dependent_n_equals_one() -> None:
    tl = step_schedule("CRF", duration_s=60.0)
    events = tl.events()
    assert len(events) == 1
    assert events[0].event_type == EVENT_RF_AFTER_RESPONSE
    assert "rf_after_response_n=1" in (events[0].label or "")


@pytest.mark.unit
def test_ext_emits_no_rf_event() -> None:
    tl = step_schedule("EXT", duration_s=60.0)
    events = tl.events()
    assert len(events) == 1
    assert events[0].event_type == EVENT_NO_RF
    assert all(e.event_type != EVENT_RF_AVAILABLE for e in events)


# ---------------------------------------------------------------------------
# Compound schedules
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_concurrent_emits_events_from_both_lanes() -> None:
    tl = step_schedule("Conc(FI 30s, FI 60s)", duration_s=120.0)
    events = tl.events()
    rf_events = [e for e in events if e.event_type == EVENT_RF_AVAILABLE]
    # FI 30s -> 30, 60, 90, 120; FI 60s -> 60, 120
    assert len(rf_events) == 6
    components = tl.components()
    assert len(components) == 2
    assert "FI 30s" in components[0]
    assert "FI 60s" in components[1]


@pytest.mark.integration
def test_mult_emits_events_per_component() -> None:
    tl = step_schedule("Mult(FI 20s, FI 40s)", duration_s=80.0)
    rf_events = [e for e in tl.events() if e.event_type == EVENT_RF_AVAILABLE]
    # 20, 40, 60, 80 + 40, 80
    assert len(rf_events) == 6


@pytest.mark.integration
def test_chain_emits_events_per_component() -> None:
    tl = step_schedule("Chain(FR 5, FI 30s)", duration_s=90.0)
    events = tl.events()
    rf_avail = [e for e in events if e.event_type == EVENT_RF_AVAILABLE]
    rf_resp = [e for e in events if e.event_type == EVENT_RF_AFTER_RESPONSE]
    # Chain has FR 5 (response-dependent annotation) and FI 30s (3 markers)
    assert len(rf_resp) == 1
    assert len(rf_avail) == 3


@pytest.mark.integration
def test_concurrent_components_have_distinct_lanes() -> None:
    tl = step_schedule("Conc(FI 30s, FI 60s)", duration_s=120.0)
    lane_labels = {ev.component for ev in tl.events()}
    assert len(lane_labels) == 2


@pytest.mark.integration
def test_nested_compound_schedules() -> None:
    tl = step_schedule("Conc(Mult(FI 10s, FI 20s), FI 30s)", duration_s=60.0)
    rf_events = [e for e in tl.events() if e.event_type == EVENT_RF_AVAILABLE]
    # Mult inner: FI 10s (6) + FI 20s (3); outer second component FI 30s (2)
    assert len(rf_events) == 11


# ---------------------------------------------------------------------------
# Parser errors and edge cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_unknown_family_raises() -> None:
    with pytest.raises(ScheduleParseError):
        step_schedule("XYZ 5", duration_s=10.0)


@pytest.mark.unit
def test_empty_schedule_raises() -> None:
    with pytest.raises(ScheduleParseError):
        step_schedule("", duration_s=10.0)


@pytest.mark.unit
def test_unbalanced_parens_raise() -> None:
    with pytest.raises(ScheduleParseError):
        step_schedule("Conc(FI 30s, FI 60s", duration_s=60.0)


@pytest.mark.unit
def test_missing_parameter_raises() -> None:
    with pytest.raises(ScheduleParseError):
        step_schedule("FI", duration_s=10.0)


@pytest.mark.unit
def test_crf_with_parameter_raises() -> None:
    with pytest.raises(ScheduleParseError):
        step_schedule("CRF 5", duration_s=10.0)


@pytest.mark.unit
def test_ratio_with_time_unit_raises() -> None:
    with pytest.raises(ScheduleParseError):
        step_schedule("FR 5s", duration_s=10.0)


@pytest.mark.unit
def test_negative_duration_raises() -> None:
    with pytest.raises(ValueError):
        step_schedule("FI 30s", duration_s=-1.0)


@pytest.mark.unit
def test_zero_duration_raises() -> None:
    with pytest.raises(ValueError):
        step_schedule("FI 30s", duration_s=0.0)


@pytest.mark.unit
def test_zero_time_step_raises() -> None:
    with pytest.raises(ValueError):
        step_schedule("FI 30s", duration_s=10.0, time_step_s=0.0)


@pytest.mark.unit
def test_unknown_combinator_raises() -> None:
    with pytest.raises(ScheduleParseError):
        step_schedule("Foo(FI 30s)", duration_s=60.0)


@pytest.mark.unit
def test_case_insensitive_family() -> None:
    tl = step_schedule("fi 10s", duration_s=30.0)
    times = [e.timestamp for e in tl.events()]
    assert times == pytest.approx([10.0, 20.0, 30.0])


@pytest.mark.unit
def test_concurrent_alias() -> None:
    tl = step_schedule("Concurrent(FI 30s, FI 60s)", duration_s=120.0)
    rf = [e for e in tl.events() if e.event_type == EVENT_RF_AVAILABLE]
    assert len(rf) == 6
