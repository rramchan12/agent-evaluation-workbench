# agent_eval

The runtime-neutral evaluation harness package. Agent runtimes own execution,
tools, and raw traces; this package owns hierarchical requirements, evidence
selection, pluggable evaluators, reconciliation, and release decisions. Inspect
AI is the first live runtime integration, not the identity of the harness.

## Subpackages

- [tasks/](./tasks/README.md) — glue: wires a scenario to Inspect's execution model
- [core/](./core/README.md) — the framework-agnostic requirement/evidence/reconciliation/release layer
- [trace/](./trace/README.md) — normalizes runtime records into the harness's trajectory model
- [evaluators/](./evaluators/README.md) — generic, config-driven evaluators, registered by ID
- [reporting/](./reporting/README.md) — renders the requirement-level evidence report

## Entry point

`cli.py` exposes two commands (also installed as the `agent-eval` console
script):

- `agent-eval run --scenario ... --task module:function --candidate ... --model ...` — live execution via Inspect, then evaluate
- `agent-eval evaluate --scenario ... --trajectory ...` — evaluator-only replay, no execution

See [ARCHITECTURE.md §5](../../ARCHITECTURE.md) for the full execution model.
See [`docs/adapters/`](../../docs/adapters/index.md) for the adapter contract.
