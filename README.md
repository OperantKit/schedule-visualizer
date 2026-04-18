# schedule-visualizer

Dry-run timeline visualizer for reinforcement-schedule DSL programs. The tool
takes a schedule expression (e.g. `"FI 30s"`, `"Conc(VI 30s, VI 60s)"`) plus a
duration and renders a horizontal timeline showing **when reinforcement would
become available** under that schedule.

## What this tool is (and is not)

- **Is**: a *dry-run* visualization of schedule availability. Time-based
  schedules (FI, VI, FT, VT) place markers at the times reinforcement becomes
  available. Compound schedules (`Conc`, `Mult`, `Chain`) lay out their
  components on separate lanes.
- **Is not**: a behavioral simulator. There is no virtual subject, no response
  stream, and no consumption of reinforcers. Ratio schedules (FR, VR) are
  inherently response-dependent, so they are rendered as annotations
  (`rf_after_response_n=N`) rather than time-located markers.

For subject-behavior simulation see the sibling `behavior-simulator` package.

## Install (development)

```bash
mise exec -- python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## CLI

```bash
schedule-visualizer --help
schedule-visualizer visualize "FI 30s" --duration 90 --output /tmp/fi.png
schedule-visualizer visualize "Conc(VI 30s, VI 60s)" --duration 120 \
    --output /tmp/conc.png --seed 7
```

## Python API

```python
from schedule_visualizer.stepper import step_schedule
from schedule_visualizer.render import render_timeline

timeline = step_schedule("FI 30s", duration_s=90.0)
render_timeline(timeline, "/tmp/fi.png")
```

## Supported schedule subset

Atomic: `FR n`, `VR n`, `RR n`, `FI t`, `VI t`, `RI t`, `FT t`, `VT t`,
`RT t`, `CRF`, `EXT`. Compound: `Conc(...)`, `Mult(...)`, `Chain(...)`.

The parser is local to this package so the visualizer has no runtime
dependency on `contingency-py` or `contingency-dsl`. Programs that use
syntax outside of this subset will raise `ScheduleParseError`.

## Status

Alpha.
