"""Tests for the matplotlib-backed renderer.

The tests verify file-output mechanics (path, PNG header, non-empty bytes)
rather than pixel-level visual correctness.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from schedule_visualizer.render import render_timeline
from schedule_visualizer.stepper import step_schedule
from schedule_visualizer.timeline import ScheduleTimeline

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


@pytest.mark.integration
def test_render_writes_png_with_correct_header(tmp_path: Path) -> None:
    tl = step_schedule("FI 10s", duration_s=30.0)
    out = tmp_path / "fi.png"
    written = render_timeline(tl, out)
    assert written == out
    assert out.exists()
    assert out.stat().st_size > 0
    with out.open("rb") as fh:
        assert fh.read(8) == PNG_HEADER


@pytest.mark.integration
def test_render_compound_schedule(tmp_path: Path) -> None:
    tl = step_schedule("Conc(FI 30s, FI 60s)", duration_s=120.0)
    out = tmp_path / "conc.png"
    render_timeline(tl, out)
    assert out.exists()
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_render_handles_empty_timeline(tmp_path: Path) -> None:
    tl = ScheduleTimeline(duration_s=60.0, schedule_str="(empty)")
    out = tmp_path / "empty.png"
    written = render_timeline(tl, out)
    assert written.exists()
    assert written.stat().st_size > 0


@pytest.mark.integration
def test_render_response_dependent_schedule(tmp_path: Path) -> None:
    tl = step_schedule("FR 5", duration_s=60.0)
    out = tmp_path / "fr.png"
    render_timeline(tl, out)
    assert out.exists()


@pytest.mark.integration
def test_render_extinction(tmp_path: Path) -> None:
    tl = step_schedule("EXT", duration_s=60.0)
    out = tmp_path / "ext.png"
    render_timeline(tl, out)
    assert out.exists()


@pytest.mark.integration
def test_render_accepts_string_path(tmp_path: Path) -> None:
    tl = step_schedule("FI 10s", duration_s=20.0)
    out = tmp_path / "via_string.png"
    written = render_timeline(tl, str(out))
    assert isinstance(written, Path)
    assert written.exists()


@pytest.mark.integration
def test_render_raises_for_missing_directory(tmp_path: Path) -> None:
    tl = step_schedule("FI 10s", duration_s=20.0)
    out = tmp_path / "does_not_exist" / "x.png"
    with pytest.raises(FileNotFoundError):
        render_timeline(tl, out)
