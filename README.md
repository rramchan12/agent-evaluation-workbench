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

This implementation was produced from an **unreviewed** plan
(`implementationReviewStatus: unreviewed` in the plan's frontmatter) — it
has not gone through the human plan-review workflow. Normal PR review, CI
checks, and branch-protection rules still apply before it is merged.

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
