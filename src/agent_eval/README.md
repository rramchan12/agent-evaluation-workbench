# agent_eval

The harness package. It never runs an agent and has no agent-framework
dependency: agents run elsewhere, and this package only reads the traces they
leave behind through adapters (`trace/`) that produce a normalized
`Trajectory`. It owns everything ARCHITECTURE.md
identifies as missing from the existing ecosystem — hierarchical requirements,
evidence selection, pluggable evaluators, reconciliation, and release
decisions. (Inspect AI was once driven from here and has been removed; see
ARCHITECTURE.md §0.)

## Subpackages

- [core/](./core/README.md) — the framework-agnostic requirement/evidence/reconciliation/release layer
- [trace/](./trace/README.md) — the harness's trajectory model and the trace adapters that produce it
- [evaluators/](./evaluators/README.md) — generic, config-driven evaluators, registered by ID
- [reporting/](./reporting/README.md) — renders the requirement-level evidence report

## Entry point

`cli.py` exposes these commands (also installed as the `agent-eval` console
script):

- `agent-eval evaluate --scenario ... --trajectory ...` — ingest a trace and evaluate it; no agent is ever executed
- `agent-eval review --report ...` — list requirements needing human review, or apply decisions
- `agent-eval calibrate --cases ...` — score a judge against hand-labeled cases

See [ARCHITECTURE.md §5](../../ARCHITECTURE.md) for the full execution model.
