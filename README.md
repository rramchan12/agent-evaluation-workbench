# Open Agent Evaluation Harness

A replay-capable evaluation harness that determines whether Cowork- and Copilot-style
agents satisfy declared requirements through an acceptable, evidenced trajectory —
not just whether their final output looks correct.

## Status

Planning and scaffolding stage. No implementation exists yet. This repository
currently contains the design documents and the folder skeleton described below;
each folder's `README.md` explains what belongs there once implementation begins.

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
