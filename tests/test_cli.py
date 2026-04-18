"""End-to-end tests for the schedule-visualizer CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from schedule_visualizer.cli import main

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


@pytest.mark.integration
def test_cli_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "schedule-visualizer" in out
    assert "visualize" in out


@pytest.mark.integration
def test_cli_visualize_writes_png(tmp_path: Path) -> None:
    out = tmp_path / "test.png"
    rc = main(
        [
            "visualize",
            "FI 30s",
            "--duration",
            "90",
            "--output",
            str(out),
        ]
    )
    assert rc == 0
    assert out.exists()
    with out.open("rb") as fh:
        assert fh.read(8) == PNG_HEADER


@pytest.mark.integration
def test_cli_visualize_with_seed_is_deterministic(tmp_path: Path) -> None:
    out_a = tmp_path / "a.png"
    out_b = tmp_path / "b.png"
    rc_a = main(
        ["visualize", "VI 30s", "--duration", "120", "--output", str(out_a), "--seed", "7"]
    )
    rc_b = main(
        ["visualize", "VI 30s", "--duration", "120", "--output", str(out_b), "--seed", "7"]
    )
    assert rc_a == 0 and rc_b == 0
    # Same seed should produce identical PNG bytes (matplotlib is deterministic
    # given identical input data and rcparams).
    assert out_a.read_bytes() == out_b.read_bytes()


@pytest.mark.integration
def test_cli_visualize_invalid_schedule_returns_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "x.png"
    rc = main(["visualize", "XYZ 5", "--duration", "10", "--output", str(out)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "could not parse" in err.lower() or "parse" in err.lower()


@pytest.mark.integration
def test_cli_visualize_invalid_duration_returns_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "x.png"
    rc = main(["visualize", "FI 30s", "--duration", "-1", "--output", str(out)])
    assert rc == 2


@pytest.mark.integration
def test_cli_visualize_missing_output_dir_returns_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "missing_subdir" / "x.png"
    rc = main(["visualize", "FI 30s", "--duration", "60", "--output", str(out)])
    assert rc == 2


@pytest.mark.integration
def test_cli_visualize_compound(tmp_path: Path) -> None:
    out = tmp_path / "conc.png"
    rc = main(
        [
            "visualize",
            "Conc(VI 30s, VI 60s)",
            "--duration",
            "120",
            "--output",
            str(out),
            "--seed",
            "11",
        ]
    )
    assert rc == 0
    assert out.exists()
