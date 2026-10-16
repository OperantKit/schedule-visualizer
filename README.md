# schedule-visualizer

:jp: [日本語版 README](README.ja.md)

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

For responding by a virtual subject, run the schedule with contingency-py and
the virtual subjects of experiment-io (see the example below).

Variable-interval and variable-time values are drawn from an exponential
distribution with the given mean, not from the Fleshler-Hoffman progression
that contingency-py uses, so a preview shows the kind of spacing, not the
exact times of a session.

## 30-second example

```bash
pip install git+https://github.com/OperantKit/schedule-visualizer
```

List the times at which each component of a concurrent schedule would make a reinforcer available during the first 2 min, and draw the timeline:

```python
from schedule_visualizer.render import render_timeline
from schedule_visualizer.stepper import step_schedule

timeline = step_schedule("Conc(FI 30s, VI 60s)", duration_s=120.0, seed=7)
for event in timeline.events():
    if event.event_type == "rf_available":
        print(round(event.timestamp, 1), event.component)
# 23.5 comp2: VI 60s
# 30.0 comp1: FI 30s
# 33.3 comp2: VI 60s
# 60.0 comp1: FI 30s
# 90.0 comp1: FI 30s
# 96.4 comp2: VI 60s
# 101.0 comp2: VI 60s
# 120.0 comp1: FI 30s
render_timeline(timeline, "conc.png")  # one lane per component
```

The FI component sets up a reinforcer every 30 s; the VI 60 s times are drawn with `seed=7`, so the output is the same on every run. To see responding and delivered reinforcers instead of availability, run the schedule with [contingency-py](https://github.com/OperantKit/contingency-py) and a virtual subject from [experiment-io](https://github.com/OperantKit/experiment-io), or with [operantkit-cli](https://github.com/OperantKit/operantkit-cli).

## Why not plot the schedule by hand?

- **One call from a schedule string to a figure.** `step_schedule` reads the same surface syntax as contingency-dsl (atomic FR, VR, RR, FI, VI, RI, FT, VT, RT, CRF, EXT; compound `Conc`, `Mult`, `Chain`) and `render_timeline` draws one lane per component.
- **Response-dependent schedules are not faked.** Ratio schedules are shown as annotations (`rf_after_response_n=N`), not as times, because their reinforcers depend on responses that a dry run does not have; `EXT` is marked as "no reinforcement".
- **Reproducible.** Variable and random schedules take a `seed`; the CLI has `--seed`.
- **Light.** The only runtime dependency is matplotlib; the parser for this subset is built in.

## Install (development)

```bash
mise exec -- python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## CLI

```bash
schedule-visualizer --help
schedule-visualizer visualize "FI 30s" --duration 90 --output fi.png
schedule-visualizer visualize "Conc(VI 30s, VI 60s)" --duration 120 \
    --output conc.png --seed 7
```

## Python API

```python
from schedule_visualizer.stepper import step_schedule
from schedule_visualizer.render import render_timeline

timeline = step_schedule("FI 30s", duration_s=90.0)
render_timeline(timeline, "fi.png")
```

## Supported schedule subset

Atomic: `FR n`, `VR n`, `RR n`, `FI t`, `VI t`, `RI t`, `FT t`, `VT t`,
`RT t`, `CRF`, `EXT`. Compound: `Conc(...)`, `Mult(...)`, `Chain(...)`.

The parser is local to this package so the visualizer has no runtime
dependency on `contingency-py` or `contingency-dsl`. Programs that use
syntax outside of this subset will raise `ScheduleParseError`.

## Status

Alpha.
