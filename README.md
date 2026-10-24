# schedule-visualizer

:jp: [日本語版 README](README.ja.md)

schedule-visualizer draws, from a schedule expression such as `Conc(FI 30s, VI 60s)`, a timeline of when each component would make a reinforcer available. It is for designing an experiment or teaching schedules: you can see the spacing of reinforcer availability before anything is run. Within [OperantKit](https://github.com/OperantKit), it previews the expressions that [schedule-writer](https://github.com/OperantKit/schedule-writer) builds and [contingency-py](https://github.com/OperantKit/contingency-py) runs.

- **From a string to a figure in two calls,** one lane per component.
- **No invented times.** Ratio schedules depend on responses, so they are labeled, not placed on the time axis.
- **Same figure every time** for a given `seed`.

## Installation

Python 3.11 or newer. schedule-visualizer is not on PyPI yet; install it from GitHub. The only dependency is matplotlib, which pip installs from PyPI.

```bash
pip install git+https://github.com/OperantKit/schedule-visualizer
```

## Example

List the times at which each component of `Conc(FI 30s, VI 60s)` makes a reinforcer available during the first 2 min, and draw the timeline:

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

The same from the command line:

```bash
schedule-visualizer visualize "Conc(FI 30s, VI 60s)" --duration 120 --seed 7 --output conc.png
```

## What it shows

| Schedule | On the timeline |
|---|---|
| `FI t`, `FT t` | A marker at t, 2t, 3t, … |
| `VI t`, `VT t` | Markers spaced by intervals drawn from an exponential distribution with mean t (`seed` fixes them) |
| `RI t`, `RT t` | A marker at each 1-s tick with probability 1/t |
| `FR n`, `VR n`, `RR n`, `CRF` | A label (`rf_after_response_n=n`), because the reinforcer depends on responses |
| `EXT` | A label "no reinforcement" |
| `Conc(...)`, `Mult(...)`, `Chain(...)` | One lane per component |

Times take the units `s`, `ms`, or `min` (`FI 30s`, `VI 2min`). Anything else raises `ScheduleParseError`.

## Limitations

- **It is not a simulation.** There is no subject and no responding. Each FI marker assumes the reinforcer is collected the moment it becomes available; in a session the next interval starts after delivery, so real times come later. To see responding and delivered reinforcers, run the schedule with contingency-py and a virtual subject from [experiment-io](https://github.com/OperantKit/experiment-io), or with [operantkit-cli](https://github.com/OperantKit/operantkit-cli).
- **VI and VT times are not the session's times.** They come from an exponential distribution, not from the Fleshler–Hoffman (1962) progression that contingency-py uses.
- **The `Mult` and `Chain` lanes are not a sequence.** Each component is laid out over the whole duration, not in the order the components would be presented.
- **Only a subset of the contingency-dsl notation is read.** `Tand`, `Alt`, changeover delays (`COD=2s`), the hyphenated units (`30-s`), annotations, and multi-phase designs are rejected. `RR n` is read as a mean ratio n; a fractional ratio value, such as the probability form `RR 0.2` that schedule-writer writes, is rejected with an error.

## For AI coding agents

Guidance for AI coding agents is in [AGENTS.md](AGENTS.md).

## Development

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/pytest
```

Every `python` block in both READMEs is run by `tests/test_readme_examples.py`.

## References

Fleshler, M., & Hoffman, H. S. (1962). A progression for generating variable-interval schedules. *Journal of the Experimental Analysis of Behavior, 5*(4), 529–530. https://doi.org/10.1901/jeab.1962.5-529

## License

MIT (declared in `pyproject.toml`).
