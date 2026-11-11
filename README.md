# Open Agent Evaluation Harness

A replay-capable evaluation harness that determines whether Cowork- and Copilot-style
agents satisfy declared requirements through an acceptable, evidenced trajectory —
not just whether their final output looks correct.

## Status

Stage 1 ("first slice") implemented: a framework-agnostic requirement /
evidence / reconciliation / release core, a generic deterministic + fake
semantic evaluator set, an Inspect AI adapter and task for the
`controlled-workspace-decision-brief` scenario, a recorded-trace path for
the `coding-agent-bugfix` scenario, a CLI (`agent-eval run` / `agent-eval
evaluate`), and a unit + integration test suite (29 tests, all passing).

This is an early (v0.1) release: the semantic evaluators are scripted fakes,
and some checks are intentionally simple (for example, required inspection is
presence-only, with no ordering evaluator yet). See
[ARCHITECTURE.md](./ARCHITECTURE.md) §0 for known deviations and the roadmap.

Licensed under the [MIT License](./LICENSE); cite via [CITATION.cff](./CITATION.cff).

## Getting started

```powershell
pip install -e .
python -m pytest -q                        # 29 unit + integration tests

# Live Inspect AI run against the decision-brief scenario, then evaluate
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
```

Both commands exit non-zero when the release decision is `FAIL`, so either
can gate a CI job.

## Start here

- [IDEATION.md](./IDEATION.md) — the research landscape survey: how agent
  evaluation has developed, the gap in existing tools, and the resulting niche.
- [ARCHITECTURE.md](./ARCHITECTURE.md) — the system design that acts on that
  niche: the system-under-test boundary, the canonical requirement/evidence
  model, the Inspect AI integration, and the staged delivery roadmap.

## Layout

```text
src/agent_eval/   the Inspect AI extension package (the harness itself)
scenarios/        declarative task definitions — the "test rack"
traces/           recorded trajectories for evaluator-only replay
expected/         ground-truth verdicts used by tests
tests/            unit and integration tests
```

See each subfolder's `README.md` for details.
