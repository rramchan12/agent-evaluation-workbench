# agent_eval

The harness package. It extends Inspect AI rather than replacing it: Inspect
owns agent execution, tools, sandboxing, and the eval log; this package owns
everything ARCHITECTURE.md identifies as missing from the existing ecosystem —
hierarchical requirements, evidence selection, pluggable evaluators,
reconciliation, and release decisions.

## Subpackages

- [tasks/](./tasks/README.md) — glue: wires a scenario to Inspect's execution model
- [core/](./core/README.md) — the framework-agnostic requirement/evidence/reconciliation/release layer
- [trace/](./trace/README.md) — normalizes Inspect's eval log into the harness's trajectory model
- [evaluators/](./evaluators/README.md) — generic, config-driven evaluators, registered by ID
- [reporting/](./reporting/README.md) — renders the requirement-level evidence report

## Entry point

A `cli.py` (not yet created) will expose two commands once implementation begins:

- `agent-eval run --scenario ... --model ...` — live execution via Inspect, then evaluate
- `agent-eval evaluate --trajectory ... --scenario ...` — evaluator-only replay, no execution

See [ARCHITECTURE.md §5](../../ARCHITECTURE.md) for the full execution model.
