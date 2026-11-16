# agent_eval

The runtime-neutral evaluation harness package. Agent runtimes own execution,
tools, and raw traces; this package owns hierarchical requirements, evidence
selection, pluggable evaluators, reconciliation, and release decisions. Inspect
AI is the first live runtime integration, not the identity of the harness.

## Subpackages

- [core/](./core/README.md) — the framework-agnostic requirement/evidence/reconciliation/release layer
- [trace/](./trace/README.md) — normalizes runtime records into the harness's trajectory model
- [evaluators/](./evaluators/README.md) — generic, config-driven evaluators, registered by ID
- [reporting/](./reporting/README.md) — renders the requirement-level evidence report

## Entry point

`cli.py` exposes these commands (also installed as the `agent-eval` console
script):

- `agent-eval evaluate --scenario ... --trajectory ...` — ingest a trace and evaluate it; no agent is ever executed
- `agent-eval review --report ...` — list requirements needing human review, or apply decisions
- `agent-eval calibrate --cases ...` — score a judge against hand-labeled cases

See [ARCHITECTURE.md §5](../../ARCHITECTURE.md) for the full execution model.
See [`docs/adapters/`](../../docs/adapters/index.md) for the adapter contract.
