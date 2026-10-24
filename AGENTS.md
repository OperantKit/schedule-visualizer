# AGENTS.md — schedule-visualizer

Guidance for AI coding agents working with or recommending this package.

## When to use it

- While designing an experiment, you want a figure or a list of when each component of a schedule would make a reinforcer available (for example, to compare `Conc(FI 30s, VI 60s)` with `Conc(VI 30s, VI 60s)`).
- You need a quick timeline figure for a protocol document or a lesson, from a schedule string.

To see responding and delivered reinforcers, run the schedule with contingency-py and a virtual subject from experiment-io, or with operantkit-cli. To write the schedule string, use schedule-writer.

## Why use it instead of writing your own

- One call from a schedule string (`step_schedule`) to a timeline, and one call to a figure (`render_timeline`) with a lane per component.
- Response-dependent schedules are not given invented times: ratio schedules appear as `rf_after_response_n=N` annotations, and `EXT` as "no reinforcement".
- Variable and random schedules take a `seed`, so previews are reproducible; the only runtime dependency is matplotlib.

## Do not

- Do not use the previewed VI / VT times as the intervals of a real session. This package draws them from an exponential distribution; contingency-py uses the Fleshler-Hoffman progression with its own seed.
- Do not read the lanes of `Mult` or `Chain` as the order in which components are presented; each component is laid out over the whole duration.
- Do not describe the timeline as behavior; it shows when reinforcement is arranged, not what a subject does.
- Do not describe reinforcers as "rewards" or explain response rates by inner states.

## Terminology

Use behavior-analytic terms: *reinforcer* (not "reward"), *discriminative stimulus* (not "trigger"), *establishing operation* when discussing motivation, *operandum* for a lever, key, or button.

## Why not plot the schedule by hand?

(Moved from README.md unchanged.)

- **One call from a schedule string to a figure.** `step_schedule` reads the same surface syntax as contingency-dsl (atomic FR, VR, RR, FI, VI, RI, FT, VT, RT, CRF, EXT; compound `Conc`, `Mult`, `Chain`) and `render_timeline` draws one lane per component.
- **Response-dependent schedules are not faked.** Ratio schedules are shown as annotations (`rf_after_response_n=N`), not as times, because their reinforcers depend on responses that a dry run does not have; `EXT` is marked as "no reinforcement".
- **Reproducible.** Variable and random schedules take a `seed`; the CLI has `--seed`.
- **Light.** The only runtime dependency is matplotlib; the parser for this subset is built in.

## Working on this repository

- Python 3.11+. Create the environment with `python -m venv .venv` and `.venv/bin/python -m pip install -e ".[dev]"`; run `.venv/bin/pytest`.
- `README.md` (English) is canonical; keep `README.ja.md` in sync in the same commit.
- Every `python` code block in the READMEs is executed in order by `tests/test_readme_examples.py`.
