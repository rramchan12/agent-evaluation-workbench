# gui/

A thin Streamlit presentation layer over the existing engine
(`agent_eval.core.engine.evaluate`) — it does not reimplement evaluation,
reporting, or release logic. It is a second caller of the same core,
exactly like `cli.py`.

```powershell
pip install -e ".[gui]"
streamlit run src/agent_eval/gui/app.py
```

## Layout

- `app.py` — Streamlit multipage entry point (sidebar + shared intro text).
- `pages/1_run.py` — select a scenario + candidate + model, launch a live
  Inspect AI run in a background thread, watch progress to completion or a
  readable error.
- `pages/2_replay.py` — select a scenario + a `traces/`-fixture or an
  uploaded trajectory/trace JSON, evaluate it directly (no Inspect AI, no
  model call).
- `results_view.py` — the shared report renderer both pages call: release
  decision banner, per-requirement cards, per-judgment rows, an evidence
  expander resolving event ids to their actual `Event`, and a visible
  "evaluators disagreed" flag.
- `scenario_catalog.py` — `discover_scenarios()` / `discover_traces()`:
  globs `scenarios/*/scenario.json` and `traces/*.json` so a new scenario or
  trace shows up without the GUI being told its id.
- `trajectory_loader.py` — loads either a saved `Trajectory` JSON or a
  recorded step-list trace JSON, auto-detected by the presence of a
  top-level `"steps"` key (mirrors `cli.py`'s `--trajectory` handling).
- `background.py` — `start_live_run(...)`: wraps the same
  `inspect_eval` -> `eval_log_to_trajectories` -> `core.engine.evaluate`
  sequence `cli.cmd_run` calls, in a background thread, reporting progress
  through a `queue.Queue[RunProgress]` and turning any exception into a
  `stage="error"` item instead of letting it crash the thread silently.
- `state.py` — `st.session_state` keys/helpers for the last result (or
  error) and the background-run handle.

`formatting.py` and `scenario_catalog.py` import no Streamlit; they are
exercised directly by `tests/unit/test_gui_formatting.py` and
`tests/unit/test_gui_scenario_catalog.py`. The page-level flows are
exercised by `tests/integration/test_gui_flows.py` using Streamlit's
`streamlit.testing.v1.AppTest` headless harness.

## Formatting

`formatting.py` holds the pure, Streamlit-free view-model helpers
(`group_by_requirement`, `has_disagreement`, `resolve_evidence`,
`verdict_badge`). `verdict_badge` reuses `reporting/render.py`'s
`_VERDICT_COLOR` table, so the GUI and the static HTML report always agree
on what PASS/FAIL/REVIEW_REQUIRED/INSUFFICIENT_EVIDENCE look like.

## Scenario content

The only change this adds to existing scenario content is one additive,
optional metadata key:
`scenarios/controlled-workspace-decision-brief/scenario.json`'s
`metadata.inspect_task` now points at
`agent_eval.tasks.decision_brief:decision_brief`, telling the Run page
which Inspect task factory to use. `coding-agent-bugfix/scenario.json` has
no `inspect_task` key, so it stays replay-only in the Run page (its only
path is the Replay page), which is its current, correct status.
