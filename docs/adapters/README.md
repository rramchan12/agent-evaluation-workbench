# Runtime adapters

The harness never runs an agent: every trace enters through an adapter. Runtime adapters translate execution records from agent runtimes and external
trace formats into the harness's canonical
[`Trajectory`](../../src/agent_eval/trace/model.py). The evaluation core only
consumes that canonical representation; it does not depend on Inspect AI,
Microsoft Agent Framework (MAF), OpenTelemetry, or any other runtime SDK.

## Ownership boundary

| Runtime or source owns | Evaluation workbench owns |
|---|---|
| Agent, model, tools, and execution | Canonical trajectory contract |
| Native messages, spans, logs, and artifacts | Evidence selection |
| Runtime-specific identifiers and metadata | Requirement evaluators |
| Capture and export of the raw run | Reconciliation and release policy |

An adapter is intentionally narrow. It preserves observable evidence and
provenance; it does not reinterpret the run, apply requirements, or manufacture
missing events.

## Supported and planned adapters

| Source | Adapter | Status |
|---|---|---|
| Inspect AI eval log | `trace/inspect_adapter.py` | Removed; candidate future adapter |
| Recorded step-list JSON | `trace/import_recorded.py` | Implemented |
| Microsoft Agent Framework trace | `trace/import_maf.py` | Planned Stage 4 integration |

See:

- [Authoring an adapter](./authoring.md)
- [Inspect AI](./inspect-ai.md)
- [Recorded JSON](./recorded-json.md)
- [Microsoft Agent Framework](./microsoft-agent-framework.md)

## Design rule

Runtime packages are optional integration dependencies, not dependencies of the
evaluation core. Importers should consume exported records without requiring the
source runtime whenever its file format makes that possible.
