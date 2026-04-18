"""Command-line interface for schedule-visualizer.

Subcommands
-----------
``visualize``
    Parse a schedule string, run the dry-run stepper for the requested
    duration, and write a PNG. Example::

        schedule-visualizer visualize "FI 30s" --duration 90 --output /tmp/fi.png
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from schedule_visualizer.render import render_timeline
from schedule_visualizer.stepper import ScheduleParseError, step_schedule


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schedule-visualizer",
        description=(
            "Dry-run timeline visualizer for reinforcement-schedule DSL "
            "programs. Shows when reinforcement would become available "
            "under a given schedule, without simulating subject behavior."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    viz = sub.add_parser(
        "visualize",
        help="Render a schedule's dry-run availability timeline to PNG.",
    )
    viz.add_argument(
        "schedule",
        help='Schedule string, e.g. "FI 30s" or "Conc(VI 30s, VI 60s)".',
    )
    viz.add_argument(
        "--duration",
        type=float,
        required=True,
        help="Length of the dry-run window, in seconds.",
    )
    viz.add_argument(
        "--output",
        required=True,
        help="Path to write the PNG to.",
    )
    viz.add_argument(
        "--time-step",
        type=float,
        default=0.1,
        help="Tick spacing for the renderer (informational). Default: 0.1s.",
    )
    viz.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for stochastic schedules (VI/RI/VR/RR). Default: random.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns the process exit code."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "visualize":
        try:
            timeline = step_schedule(
                args.schedule,
                duration_s=args.duration,
                time_step_s=args.time_step,
                seed=args.seed,
            )
        except ScheduleParseError as exc:
            print(f"error: could not parse schedule: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        out_path = Path(args.output)
        try:
            written = render_timeline(timeline, out_path)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(str(written))
        return 0

    # argparse with required=True on the subparsers should make this
    # unreachable, but guard anyway.
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
