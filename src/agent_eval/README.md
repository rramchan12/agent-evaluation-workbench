# agent_eval

The runtime-neutral evaluation harness package. It never runs an agent:
agent runtimes own execution, tools, and raw traces, and this package reads the
trace they leave behind through adapters (`trace/`). It owns hierarchical
requirements, evidence selection, pluggable evaluators, reconciliation, and
release decisions. (Inspect AI was once driven from here and has been removed;
see ARCHITECTURE.md §0.)

## Subpackages

- [core/](./core/README.md) — the framework-agnostic requirement/evidence/reconciliation/release layer
- [trace/](./trace/README.md) — the trace adapters that normalize runtime records into the harness's trajectory model
- [evaluators/](./evaluators/README.md) — generic, config-driven evaluators, registered by ID
- [reporting/](./reporting/README.md) — renders the requirement-level evidence report

## Entry point

`cli.py` exposes these commands (also installed as the `agent-eval` console
script):

- `agent-eval evaluate --scenario ... --trajectory ...` — ingest a trace and evaluate it; no agent is ever executed
- `agent-eval review --report ...` — list requirements needing human review, or apply decisions
- `agent-eval calibrate --cases ...` — score a judge against hand-labeled cases

See [ARCHITECTURE.md §5](../../ARCHITECTURE.md) for the full execution model.
See [`docs/adapters/`](../../docs/adapters/README.md) for the adapter contract.
