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
- `pages/1_replay.py` — select a scenario + a `traces/`-fixture or an
  uploaded trajectory/trace JSON, evaluate it directly (no agent, no
  model call).
- `pages/2_review.py` — Stage 3 human review: lists requirements at
  `REVIEW_REQUIRED` / `INSUFFICIENT_EVIDENCE` (from the last Replay
  result or an uploaded `report.json`), records a reviewer verdict, and
  recomputes the release decision with `apply_human_review` (same as
  `agent-eval review`).
- `pages/3_calibration.py` — Stage 3 judge calibration: runs
  `scenarios/*/cases.json` (or an upload) through `run_calibration_file`
  and shows accuracy against a minimum threshold (same as
  `agent-eval calibrate`).
- `results_view.py` — the shared report renderer the pages call: release
  decision banner, per-requirement cards, per-judgment rows, an evidence
  expander resolving event ids to their actual `Event`, and a visible
  "evaluators disagreed" flag.
- `scenario_catalog.py` — `discover_scenarios()` / `discover_traces()`:
  globs `scenarios/*/scenario.json` and `traces/*.json` so a new scenario or
  trace shows up without the GUI being told its id.
- `trajectory_loader.py` — loads either a saved `Trajectory` JSON or a
  recorded step-list trace JSON, auto-detected by the presence of a
  top-level `"steps"` key (mirrors `cli.py`'s `--trajectory` handling).
- `state.py` — `st.session_state` keys/helpers for the last result (or
  error).

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

The GUI adds nothing to scenario content: every scenario is evaluated by
replaying a trace, and there is no live-run page because the harness never
runs an agent.
