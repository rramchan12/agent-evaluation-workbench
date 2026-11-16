# trace/

Normalizes runtime-specific execution records into the harness's canonical
trajectory model. Runtime details stop at this package boundary; `core/` and
`evaluators/` consume only `Event` and `Trajectory`.

Modules:

- `model.py` — the normalized trace event / artifact / trajectory records
  (`Event`, `Trajectory`) that `core/` consumes, with JSON save/load.
- `import_recorded.py` — recorded step-list JSON (no runtime involved) ->
  `Trajectory`. Used by every fixture under `traces/` (coding-agent-bugfix and
  the decision-brief pair).
- `import_maf.py` (planned) — Microsoft Agent Framework trace export ->
  normalized `Trajectory`, without requiring MAF at evaluation time.
- `otel_export.py` (not yet implemented) — would export harness results
  *out* to OpenTelemetry / OpenInference-compatible observability tools.

The authoritative adapter boundary and conformance rules live in
[`docs/adapters/`](../../../docs/adapters/README.md).
