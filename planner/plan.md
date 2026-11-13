---
status: final
sectionOrder: [testing]
topPlanId: ff4b65a9-669c-e9f8-6a52-edde6433e17d
planSourceId: 39f48528-7ecb-4888-be1d-bb46de1e824c
planSyncOwner: "github:rramchan12/agent-evaluation-workbench"
sourceIssueUrl: "https://github.com/rramchan12/agent-evaluation-workbench/issues/3"
---
# Plan: Evaluation GUI + research-aligned README

## Business & features

### Why this matters

The harness (Stage 1, merged to `main`) already proves the end-to-end
contract — requirement-level evidence, deterministic + semantic evaluators,
reconciliation, release decisions, evaluator-only replay — but every
interaction with it today is CLI-only: `agent-eval run` and `agent-eval
evaluate`, text output, and a static `report.html` file you have to open
separately. There is no way for someone unfamiliar with the CLI flags, the
JSON report shape, or the requirement model to explore a result interactively.

This plan adds a GUI that sits *in front of* the existing engine — it does
not reimplement evaluation, reporting, or release logic — and refreshes the
README so a new reader understands both the architecture and how to actually
run the thing, backed by real screenshots instead of a text description.

### User-facing capabilities (from the acceptance criteria)

1. **Launch an evaluation.** Pick a scenario (`controlled-workspace-decision-brief`
   today; GUI must generalize to any scenario folder under `scenarios/` that
   ships an Inspect task + candidate), pick/configure a candidate and model,
   start a live Inspect AI run, and watch progress through to completion or a
   clear, actionable error (e.g. missing API key, Inspect task crash, invalid
   scenario JSON).
2. **Replay a recorded trajectory.** Pick a scenario and either an existing
   fixture under `traces/` or an uploaded trajectory/recorded-trace JSON, run
   `core.engine.evaluate` directly — no Inspect AI, no model call — and show
   the same report UI. This is the GUI's path to Definition-of-Done item 5
   (evaluator-only replay) and doubles as the UI for the `coding-agent-bugfix`
   scenario, which has no Inspect task yet.
3. **Understand the result.** One screen shows: the release decision badge,
   each requirement with its verdict, every evaluator judgment that fed it
   (with disagreement visible when evaluators split), the evidence event ids
   each judgment cites (resolved to their actual tool-call content, not just
   ids), and any `INSUFFICIENT_EVIDENCE` / incomplete-trajectory reasons.

### Out of scope for this change

- No new evaluators, requirement kinds, reconciliation rules, or release
  policy changes — the GUI is a consumer of `core.engine.evaluate`, exactly
  like the CLI.
- No change to Inspect AI's own execution/transcript viewer (`inspect view`);
  the GUI does not try to re-render Inspect's native log.
- No authn/authz, multi-user state, or hosted deployment — this is a local
  developer tool, run the same way `agent-eval` is: `pip install -e .` then
  launch a Streamlit app.
- No new scenario content — the GUI must work with the two scenarios that
  exist today and generalize to future ones without being told their ids.

## Architecture

### Key decision: Streamlit, as a thin presentation layer over the existing engine

Confirmed with the user: Streamlit (Python-only). Rationale over the
alternatives considered:

| Option | Why not chosen |
|---|---|
| FastAPI + HTML/JS frontend | More total code (API layer + a hand-rolled frontend) for a local dev tool; no separate frontend build/test story needed yet |
| Gradio | Narrower widget set for the kind of structured, nested, multi-section report view this needs (per-requirement cards, evidence drill-down) |
| Streamlit (chosen) | Single language, reuses `agent_eval` as a library import, fastest to iterate and to screenshot for the README |

The GUI is a **new top-level entry point**, not a change to the harness core:

```text
src/agent_eval/gui/
    app.py              Streamlit entry point (``streamlit run``)
    pages/
        1_run.py        Launch screen: select scenario + candidate/model, start, progress
        2_replay.py      Replay screen: select scenario + trajectory source, evaluate
        3_results.py     Shared results view used by both flows (or a results component imported by both)
    state.py            Session-state helpers (background run tracking, result caching)
    background.py       Thread-based runner + progress queue for the live-run path
    scenario_catalog.py Discovers scenarios/*/scenario.json and candidates
    formatting.py       Pure helpers: Report -> view-model (no Streamlit import), reused by tests
```

This lives inside `src/agent_eval` (not a sibling top-level package) because
it **imports** `agent_eval.core.engine.evaluate`, `agent_eval.core.requirements.load_scenario`,
`agent_eval.trace.model.Trajectory`, `agent_eval.trace.import_recorded.import_recorded_trace`,
and (only for the live-run path) `agent_eval.trace.inspect_adapter.eval_log_to_trajectories`
and the scenario's Inspect task factory — the same calls `cli.py` makes. The
GUI and the CLI become two callers of one unchanged core; nothing in
`core/`, `evaluators/`, or `trace/` changes.

```text
                     ┌───────────────────────────┐
                     │   agent_eval.core.engine   │
                     │     evaluate(scenario,     │
                     │              trajectory)   │
                     └─────────────▲──────────────┘
                                   │  same call, both callers
            ┌──────────────────────┴───────────────────────┐
            │                                               │
   ┌────────┴────────┐                            ┌─────────┴─────────┐
   │   cli.py (CLI)  │                            │  gui/app.py (new)  │
   │  run / evaluate │                            │  Run / Replay tabs │
   └─────────────────┘                            └────────────────────┘
```

### Key decision: background execution for the live-run path

Streamlit's execution model reruns the whole script top-to-bottom on every
interaction and blocks on a long-running call in the main thread — an
Inspect AI run of even a few tool-call steps is seconds, but must not freeze
the UI with no feedback, and must surface Inspect's own errors (crashed
model, exception from a tool, scenario misconfiguration) as a message, not a
stack trace in the terminal the user can't see.

Decision: run the Inspect call in a background `threading.Thread`, report
coarse-grained progress via a thread-safe `queue.Queue` of status strings
(`"starting inspect eval…"`, `"evaluating requirements…"`, `"done"`, or an
error payload), and have the Streamlit page poll the queue on a short
`st.rerun()` timer while the thread is alive. This reuses the *existing*
`cli.cmd_run`/`cmd_evaluate` call shape (`inspect_eval(...)` then
`eval_log_to_trajectories(...)` then `run_engine(...)`) — the GUI calls the
same library functions `cli.py` calls, not `cli.py` itself as a subprocess,
so there is one evaluation code path, not two.

Alternative considered and rejected: shelling out to `agent-eval run` as a
subprocess and tailing its stdout. Rejected because it would duplicate the
CLI's argument-building logic in the GUI and make structured progress/error
reporting harder (parsing printed text instead of catching a Python
exception with a traceback the GUI can show truncated, with a "show details"
expander).

### Key decision: scenario/candidate discovery is dynamic, not hardcoded

The GUI must not hardcode `controlled-workspace-decision-brief` or
`coding-agent-bugfix`. `scenario_catalog.py` globs `scenarios/*/scenario.json`,
loads each with the existing `load_scenario`, and separately inspects the
scenario folder for a `candidates/` directory (live-run capable, needs an
Inspect task) versus none (replay-only, e.g. `coding-agent-bugfix` today).
The GUI reads which Inspect task factory to use from scenario `metadata`
(new, optional `metadata.inspect_task` field, e.g.
`"agent_eval.tasks.decision_brief:decision_brief"`) falling back to "no live
run available, replay only" when absent — this mirrors `cli.py`'s existing
`--task module.path:function_name` convention (`_resolve_task_factory`)
instead of inventing a second one. Adding this one optional metadata key to
`scenarios/controlled-workspace-decision-brief/scenario.json` is the only
change to existing scenario content.

### Key decision: model choice for a live run defaults to the safe/free path

The CLI already defaults `--model` to `mockllm/model` (scripted, no network
call, no cost). The GUI's Run screen keeps that default and only exposes a
free-text "model" override (same semantics as `agent-eval run --model`) for
someone who has credentials configured — it never silently calls a paid
model. This avoids a surprise cost/latency and needs no new confirmation
dialog since the default is already inert.

### Data flow summary

```text
Run tab:     scenario.json ──┐
             candidate.json ─┼─> decision_brief(candidate_path) [Inspect Task]
             model name ─────┘         │
                                  inspect_eval(...)
                                        │
                              eval_log_to_trajectories(...)
                                        │
                                 Trajectory  ──────────────┐
                                                            │
Replay tab:  scenario.json ──┐                             │
             trajectory/     ├─> import_recorded_trace() ──┤
             trace JSON ─────┘    or Trajectory.from_dict() │
                                                            ▼
                                              core.engine.evaluate(scenario, trajectory)
                                                            │
                                                         Report
                                                            │
                                                 formatting.py view-model
                                                            │
                                                  results page (shared)
```

## Components & modules

| Module (new unless noted) | Responsibility |
|---|---|
| `src/agent_eval/gui/app.py` | Streamlit multipage entry point; sidebar scenario picker shared across pages |
| `src/agent_eval/gui/pages/1_run.py` | Form: scenario, candidate (from `scenario_catalog`), model (default `mockllm/model`), optional `--log-dir`/save-trajectory path; "Run evaluation" button; progress panel; routes to results on completion |
| `src/agent_eval/gui/pages/2_replay.py` | Form: scenario, trajectory source (dropdown over `traces/*.json` plus a file-uploader for an arbitrary trajectory/trace JSON); "Evaluate" button; routes to results |
| `src/agent_eval/gui/pages/3_results.py` or `gui/components/results_view.py` | Renders a `Report`: release-decision banner, per-requirement cards (verdict, importance, kind, description), per-judgment rows (evaluator id, kind, verdict, explanation, confidence), evidence-event expander resolving ids to the actual `Event` (tool name/arguments/result) via `Trajectory.event(id)`, and a visible "evaluators disagreed" flag when a requirement's judgments contain more than one distinct verdict |
| `src/agent_eval/gui/state.py` | `st.session_state` keys/helpers: last `Report` + `Trajectory`, background-thread handle, progress queue, error payload |
| `src/agent_eval/gui/background.py` | `start_live_run(scenario_path, task_factory, candidate_path, model, log_dir) -> (Thread, Queue)`; wraps the existing `inspect_eval` → `eval_log_to_trajectories` → `run_engine` sequence; catches and formats exceptions instead of letting them escape the thread silently |
| `src/agent_eval/gui/scenario_catalog.py` | `discover_scenarios() -> list[ScenarioInfo]` (id, name, path, candidates, inspect_task or None); `discover_candidates(scenario_dir)`; `discover_traces(scenario_id)` for the replay dropdown |
| `src/agent_eval/gui/formatting.py` | Pure, Streamlit-free helpers turning a `Report`/`Trajectory` into display-ready structures (verdict → color/label, judgment grouping per requirement, evidence resolution) — this is what unit tests target without a Streamlit test harness |
| `src/agent_eval/cli.py` | Unchanged; GUI does not modify it. `_resolve_task_factory` logic is duplicated narrowly in `scenario_catalog.py` only because it's an 8-line pure function, not imported, to avoid making `cli.py` an import dependency of the GUI package for an unrelated reason |
| `scenarios/controlled-workspace-decision-brief/scenario.json` | One additive change: `metadata.inspect_task` pointing at `agent_eval.tasks.decision_brief:decision_brief` |
| `pyproject.toml` | New `gui` optional-dependency extra (`streamlit`); new console entry point or documented `streamlit run` command |
| `README.md` | New "GUI" section: setup, walkthrough, screenshots (see Code & files) |
| `tests/unit/test_gui_formatting.py` (new) | Unit tests for `formatting.py` against fixtures already in `expected/`/`traces/` |
| `tests/integration/test_gui_flows.py` (new) | Streamlit `AppTest` (from `streamlit.testing.v1`) driving the Run and Replay pages end-to-end against the real engine, no network |
| `docs/screenshots/` (new) | Repository-hosted PNGs referenced by the README (see Code & files) |

## Testing <!-- layer:testing desc="GUI test coverage: run/replay flows, pass/fail/insufficient-evidence/error states, screenshot capture approach" -->

### Test strategy

Two layers, matching the two kinds of logic the GUI introduces:

1. **Pure-function unit tests (`formatting.py`, `scenario_catalog.py`)** — no
   Streamlit runtime involved, these run under plain `pytest` like the
   existing suite. They cover: verdict → badge mapping, grouping judgments by
   requirement, flagging disagreement (>1 distinct verdict on one
   requirement's judgments), resolving an evidence event id to its `Event`,
   and scenario/candidate/trace discovery against the real `scenarios/` and
   `traces/` directories (so a new scenario or trace file doesn't silently
   stop showing up).
2. **Page-level flow tests**, using `streamlit.testing.v1.AppTest` (Streamlit's
   official headless test harness — no browser, no screenshots, asserts on
   the app's widget tree and session state). These exercise:
   - **Replay flow, PASS**: select `controlled-workspace-decision-brief` +
     `traces`-equivalent saved-trajectory fixture (or `expected/`-backed
     candidate) that is known to pass every requirement; assert the release
     banner reads `PASS` and every requirement card shows `PASS`.
   - **Replay flow, FAIL**: same scenario with `candidate-1`'s trajectory
     (known blocker/major failures per `ARCHITECTURE.md` §7); assert the
     release banner reads `FAIL` and the failing requirement(s) are visible
     with their failing judgment's explanation text.
   - **Replay flow, INSUFFICIENT_EVIDENCE**: feed a trajectory JSON with
     `"complete": false` (new small fixture); assert the banner and the
     affected requirement(s) show `INSUFFICIENT_EVIDENCE`, not a silent pass.
   - **Replay flow, malformed input error**: upload invalid JSON / a
     JSON missing required `Trajectory` fields; assert the page shows a
     readable error message instead of raising an uncaught exception in the
     app (Streamlit would otherwise render its own traceback box — the test
     asserts *our* message appears, not Streamlit's default).
   - **Run flow, happy path**: launch against `candidate-2` with
     `mockllm/model` (free, deterministic, no network); poll until the
     background thread reports completion; assert the same results view
     renders with `PASS`.
   - **Run flow, task error**: point the Run form at a deliberately broken
     candidate path (nonexistent file); assert the background-thread error
     path surfaces as a readable message, not a hang or a bare stack trace.
3. **Screenshot capture is separate from automated tests.** Screenshots for
   the README are produced by a small, repeatable script
   (`scripts/capture_screenshots.py`, Playwright driving a locally-launched
   `streamlit run` process) that runs the Run-happy-path and a
   Replay-FAIL-with-disagreement scenario and saves PNGs into
   `docs/screenshots/`. This script is not part of `pytest`/CI — it is a
   documented, manually-invoked step (README-authoring time only) because
   screenshots are for human-readable documentation, not a correctness
   check; the `AppTest` suite above is what actually gates correctness in
   CI/local test runs.

### Fixtures needed (new, small, additive — no change to existing fixtures)

- `traces/decision-brief-pass.json` or reuse of the existing
  `candidates/candidate-2.json` path through a live mock run — prefer running
  `candidate-2` live (already proven to PASS by `tests/integration/test_decision_brief_scenario.py`)
  over inventing a new static fixture, to avoid a second source of truth.
- `traces/coding-bugfix-insufficient.json` (new): a trimmed copy of
  `traces/coding-bugfix-good.json` with `"complete": false` and an
  `"incompleteness_reason"`, to exercise the `INSUFFICIENT_EVIDENCE` view
  without inventing a new scenario.

## Code & files

### New package: `src/agent_eval/gui/`

- `app.py` — `st.set_page_config`, sidebar, imports pages via Streamlit's
  multipage convention (`pages/` directory with numeric prefixes controls
  sidebar order: Run before Replay).
- `scenario_catalog.py`:
  ```python
  @dataclass
  class ScenarioInfo:
      id: str
      name: str
      path: Path
      candidates: list[Path]          # scenarios/<id>/candidates/*.json, [] if none
      inspect_task: str | None        # metadata.inspect_task, None => replay-only

  def discover_scenarios(scenarios_dir: Path = SCENARIOS_DIR) -> list[ScenarioInfo]: ...
  def discover_traces(traces_dir: Path = TRACES_DIR, scenario_id: str | None = None) -> list[Path]: ...
  ```
- `background.py`:
  ```python
  @dataclass
  class RunProgress:
      stage: str                      # "starting" | "running" | "evaluating" | "done" | "error"
      report: Report | None = None
      trajectory: Trajectory | None = None
      error: str | None = None        # formatted exception, traceback kept in .detail for an expander

  def start_live_run(scenario_path, task_factory_dotted, candidate_path, model, log_dir) -> tuple[Thread, Queue[RunProgress]]: ...
  ```
  Internally calls, in order, exactly what `cli.cmd_run` calls:
  `load_scenario` → `_resolve_task_factory`-equivalent → `inspect_eval` →
  `eval_log_to_trajectories` → `core.engine.evaluate`, pushing a `RunProgress`
  onto the queue before/after each stage and wrapping the whole body in
  `try/except Exception` so a crash becomes a `stage="error"` item, never an
  unhandled thread exception.
- `formatting.py`:
  ```python
  def verdict_badge(verdict: str) -> tuple[str, str]: ...     # (label, color), reuses reporting/render.py's _VERDICT_COLOR constants (imported, not copied)
  def group_by_requirement(report: Report) -> list[RequirementView]: ...
  def has_disagreement(judgments: list[Judgment]) -> bool: ...
  def resolve_evidence(trajectory: Trajectory, event_ids: list[str]) -> list[Event]: ...
  ```
  Reuses `agent_eval.reporting.render._VERDICT_COLOR` rather than redefining
  verdict colors a second time, so the GUI and the static HTML report always
  agree on what PASS/FAIL/etc. look like.
- `pages/1_run.py`, `pages/2_replay.py`: Streamlit forms + `st.session_state`
  wiring to `background.py`/`core.engine.evaluate` and `formatting.py`;
  render the shared results component from `pages/3_results.py` (imported as
  a function, not a third page, if Streamlit's multipage routing makes a
  silent third sidebar entry undesirable — final file split decided during
  implementation, not a material planning decision).

### Scenario content change

- `scenarios/controlled-workspace-decision-brief/scenario.json`: add
  `"metadata": {..., "inspect_task": "agent_eval.tasks.decision_brief:decision_brief"}`.
  `coding-agent-bugfix/scenario.json` gets no `inspect_task` key (stays
  replay-only), which is exactly its current, correct status.

### Packaging

- `pyproject.toml`: add
  ```toml
  [project.optional-dependencies]
  gui = ["streamlit>=1.38"]
  ```
  Document `pip install -e ".[gui]"` then `streamlit run src/agent_eval/gui/app.py`
  in the README; no new console-script entry point needed (Streamlit's own
  CLI launches it).

### README rewrite

- New "## GUI" section (after "## Getting started", before "## Start here"):
  install step (`pip install -e ".[gui]"`), launch command, a short
  walkthrough ("Run tab: pick a scenario and candidate, click Run, watch
  progress, read the release decision and requirement verdicts. Replay tab:
  point at a recorded trajectory, get the same view with zero model calls."),
  and 2–3 embedded screenshots from `docs/screenshots/` (Run-in-progress or
  Run-complete-PASS, and Replay-FAIL-with-disagreement, to show both a
  passing and a failing/disagreeing report).
- New "## Architecture, in plain language" section replacing none of the
  existing content but sitting alongside the existing "Start here" links:
  explains the requirement → evidence → judgment → reconciliation →
  release pipeline in a few plain sentences, keeps the existing vocabulary
  (Requirement, Evidence, Judgment, Reconciliation, Release decision —
  no renaming), states explicitly that "Inspect AI owns execution and its
  own trace/log viewer; this harness and its GUI own requirement evidence
  and the release decision" (mirrors `ARCHITECTURE.md` §6's ownership
  table), and links to `ARCHITECTURE.md` (system boundary, §6 ownership
  table) and `IDEATION.md` (why a requirement-level, evidence-backed
  evaluator is the gap this project fills) at the specific points in the
  explanation they support, not just as a trailing link list.
- "## Layout" code block gets one added line: `src/agent_eval/gui/   the Streamlit evaluation GUI`.
- "## Status" paragraph gets one added sentence noting the GUI addition and
  the updated test count once implemented.

### Documentation assets

- `docs/screenshots/run-complete-pass.png`
- `docs/screenshots/replay-fail-disagreement.png`
- `scripts/capture_screenshots.py` (Playwright-based capture helper, documented
  as a manual/one-off tool, not part of `pytest`)

## Tasks

1. Build the GUI (scenario/trace discovery, Run tab with background execution and progress/error handling, Replay tab, shared results view reusing `core.engine`/`reporting` colors, the one additive `inspect_task` metadata key, `pyproject.toml` `gui` extra) with unit tests for `formatting.py`/`scenario_catalog.py` and `AppTest` flow tests covering PASS, FAIL, INSUFFICIENT_EVIDENCE, and error states for both Run and Replay — depends on: none
2. Capture repository-hosted screenshots (`scripts/capture_screenshots.py` + `docs/screenshots/*.png`) and rewrite the README (GUI setup/walkthrough/screenshots, plain-language architecture section linking ARCHITECTURE.md/IDEATION.md, updated layout/status) — depends on: 1
