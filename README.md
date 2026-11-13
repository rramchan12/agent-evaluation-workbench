# Open Agent Evaluation Harness

A replay-capable evaluation harness that determines whether Cowork- and Copilot-style
agents satisfy declared requirements through an acceptable, evidenced trajectory —
not just whether their final output looks correct.

## Status

Stages 1 through 3 are implemented: a requirement, evidence, reconciliation,
and release core that has no dependency on any particular agent runtime; a
generic deterministic and semantic evaluator set, made up of a deterministic
`fake_judge` and a real model-backed `real_judge`; a runtime adapter and task
for the `controlled-workspace-decision-brief` scenario, currently built
against Inspect AI as the first runtime this project integrates with; a
recorded-trace path for the `coding-agent-bugfix` scenario that needs no
runtime at all; judge calibration and human-review CLI commands; a CLI
(`agent-eval run`, `agent-eval evaluate`, `agent-eval review`, and
`agent-eval calibrate`); a Streamlit GUI for the run and replay flows; and a
unit and integration test suite of 85 tests, all passing.

This is an early (v0.1) release: some checks are intentionally simple (for
example, required inspection is presence-only, with no ordering evaluator
yet), and human review is applied post-hoc over a persisted report rather
than as a scenario-declared evaluator assignment. See
[ARCHITECTURE.md](./ARCHITECTURE.md) §0 for known deviations and the roadmap.

Licensed under the [MIT License](./LICENSE); cite via [CITATION.cff](./CITATION.cff).

## Getting started

```powershell
pip install -e .
python -m pytest -q                        # 85 unit + integration tests

# A live run through the current runtime adapter (Inspect AI) against the
# decision-brief scenario, then evaluate
agent-eval run `
  --scenario scenarios/controlled-workspace-decision-brief/scenario.json `
  --task agent_eval.tasks.decision_brief:decision_brief `
  --candidate scenarios/controlled-workspace-decision-brief/candidates/candidate-2.json `
  --model mockllm/model `
  --out-dir out

# Evaluator-only replay (no agent execution) against a saved trajectory
agent-eval evaluate `
  --scenario scenarios/coding-agent-bugfix/scenario.json `
  --trajectory traces/coding-bugfix-good.json `
  --out-dir out

# Score a judge against a hand-labeled calibration fixture
agent-eval calibrate --cases scenarios/judge-calibration/cases.json

# List requirements still needing human review in a saved report, or
# apply decisions and recompute the release
agent-eval review --report out/report.json
agent-eval review --report out/report.json --decisions decisions.json --out-dir out
```

Both `run` and `evaluate` exit non-zero when the release decision is `FAIL`,
so either can gate a CI job; `calibrate` exits non-zero when accuracy falls
below `--min-accuracy` (default 1.0).

## GUI

A Streamlit GUI sits in front of the same evaluation engine the CLI uses —
no separate evaluation logic, just a different front door onto `agent_eval`.

```powershell
pip install -e ".[gui]"
streamlit run src/agent_eval/gui/app.py
```

It has two pages, reachable from the sidebar:

- **Run** — pick a scenario and candidate, launch a live evaluation through
  the current runtime adapter (Inspect AI, with a scripted and free
  `mockllm/model` by default) in a background thread, and watch the same
  release decision and per-requirement report the CLI would produce,
  rendered live.
- **Replay** — pick a scenario and upload a saved trajectory or recorded
  step-list trace JSON (no agent execution, no model calls) to replay it
  through the evaluators and see the resulting report — useful for
  iterating on requirements/evaluators against a trace you already have.

Run tab, `controlled-workspace-decision-brief` + `candidate-2`, a clean PASS:

![Run tab: a clean PASS](docs/screenshots/run-complete-pass.png)

Replay tab, the same scenario + `candidate-1`'s trajectory, an overall FAIL
with one requirement where the deterministic and semantic evaluators
disagreed:

![Replay tab: FAIL with evaluator disagreement](docs/screenshots/replay-fail-disagreement.png)

## Architecture, in plain language

Every scenario declares a small set of **requirements** — obligations,
prohibitions, and verifications — that an agent's run must satisfy. While
the agent works, the runtime it is executing on records what actually
happened as a **trajectory** of tool calls and results, and that trajectory
is the **evidence** this harness evaluates. For each requirement, one or
more **evaluators** examine the relevant evidence and each return an
independent **judgment** of `PASS`, `FAIL`, `REVIEW_REQUIRED`, or
`INSUFFICIENT_EVIDENCE`. When more than one evaluator judges the same
requirement, **reconciliation** resolves any disagreement into a single
verdict for that requirement (see [ARCHITECTURE.md
§6](./ARCHITECTURE.md#6-responsibility-split-between-the-harness-and-the-agent-runtime) for exactly
which evaluator wins and why), and a **release decision** then rolls every
requirement's verdict up into one pass-or-fail outcome for the whole run.

The diagram below shows where the boundary sits. The agent runtime owns
execution and the raw record of what happened; this harness and its GUI own
requirement evidence, judgment reconciliation, and the release decision, and
that half of the system has no dependency on any particular runtime. Inspect
AI is simply the first runtime this boundary has been proven against,
through `trace/inspect_adapter.py`; the same boundary is what should let a
second runtime, such as the Microsoft Agent Framework, plug in through its
own adapter without any change to `core/` or `evaluators/` (see
[ARCHITECTURE.md §8, Stage
4](./ARCHITECTURE.md#stage-4-ecosystem-integration--next)).

```mermaid
flowchart LR
    SCENARIO["Scenario<br/>Requirements + Fixtures"] --> RUNTIME
    SCENARIO --> EVALUATE

    subgraph RUNTIME["Agent runtime (swappable)"]
        direction TB
        INSPECT["Inspect AI<br/>in use today"]
        MAF["Microsoft Agent Framework<br/>Stage 4 target"]
    end

    RUNTIME -->|trajectory| EVALUATE["Evaluation core<br/>Evidence · Evaluators · Reconciliation"]
    EVALUATE --> RESULT["Release decision + report"]

    style RUNTIME fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#172554
    style EVALUATE fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#3b0764
    style RESULT fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#450a0a
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system design behind
this pipeline, and [IDEATION.md](./IDEATION.md) for the research gap it was
built to fill.

## How this compares

[CAPABILITY_DISCOVERY.md](./CAPABILITY_DISCOVERY.md) checked seven
candidate runtimes and evaluation libraries against the requirement, evidence,
judgment, reconciliation, and release chain this harness implements, using
only documentation and canonical repositories as sources. The summary table
below is reproduced from that document; see it for sources, per-framework
detail, and the classification method.

| Framework | Native strength | Stored-run evaluation | Repetition | Stateful execution and HITL | Disagreement and abstention | CI gate | Local without hosted account |
|---|---|---|---|---|---|---|---|
| Microsoft Agent Framework | Agent/workflow runtime, local evaluators, tool checks | Existing responses are native; full trace evaluation uses Foundry | Native | Native checkpoints and approvals | Custom; Foundry has limited `not_applicable` behavior | Native assertions | Yes for deterministic checks |
| Google ADK | Eval sets, tool trajectories, graph workflows | Open-source evaluator reruns the agent; historical trace scoring is hosted or custom | Native | Native graph state and confirmations | Per-metric results; reconciliation is custom | Native CLI and pytest | Basic deterministic metrics |
| LangGraph | Stateful graph runtime, checkpoints, retries, interrupts | Provided by LangSmith, not LangGraph | Custom or LangSmith | Native | Custom | Custom or LangSmith | Yes |
| LangSmith | Datasets, traces, evaluators, experiments | Native evaluation of existing experiments | Native | Human annotation, not runtime approval | Partial; no verified first-class adjudication or abstention policy | Native integrations; policy is custom | Partial |
| Inspect AI | Local evaluation runtime, sandboxes, scorers, logs | Native rescoring of stored logs | Native | Native checkpoints and approvals | Native scorer panels, agreement metrics, and unscored results | Quality thresholds require custom policy | Yes |
| Pydantic Evals | Typed Python evaluations and span evaluators | Native evaluator replay primitive; persistence is custom | Native | Arbitrary Python tasks; workflow engine is custom | Custom; Logfire adds human review | Custom | Yes |
| Promptfoo | Declarative assertions, CI, reports, red teaming | Historical output replay is native; exported trace regrading is unknown | Native | Native sequential conversations | Custom | Native exit codes | Yes |

None of the seven frameworks implements the full requirement-to-release
chain natively, and every one of them is weakest at the same point: turning
disagreement between evaluators, or missing evidence, into an explicit,
first-class outcome rather than a silently averaged score. That shared gap
is the reason this project exists as a layer on top of a runtime rather than
as a new runtime itself.

## Start here

- [IDEATION.md](./IDEATION.md) — the research landscape survey: how agent
  evaluation has developed, the gap in existing tools, and the resulting niche.
- [ARCHITECTURE.md](./ARCHITECTURE.md) — the system design that acts on that
  niche: the system-under-test boundary, the canonical requirement/evidence
  model, the runtime adapter model (Inspect AI today), and the staged
  delivery roadmap.
- [CAPABILITY_DISCOVERY.md](./CAPABILITY_DISCOVERY.md) — the sourced,
  per-framework detail behind the comparison table above, including
  citations and the classification method.
- [BENCHMARK_PLAN.md](./BENCHMARK_PLAN.md) — the planned, ten-trace,
  seven-framework benchmark that will eventually turn that comparison into
  measured evidence. Stage 4's near-term scope (one framework, one trace
  pair, one new adapter — see [ARCHITECTURE.md
  §8](./ARCHITECTURE.md#stage-4-ecosystem-integration--next)) is a smaller,
  concrete first slice of this larger plan, not a replacement for it.

## Layout

```text
src/agent_eval/   the evaluation harness package (its first runtime adapter targets Inspect AI)
src/agent_eval/gui/   the Streamlit evaluation GUI
scenarios/        declarative task definitions — the "test rack"
traces/           recorded trajectories for evaluator-only replay
expected/         ground-truth verdicts used by tests
tests/            unit and integration tests
```

See each subfolder's `README.md` for details.
