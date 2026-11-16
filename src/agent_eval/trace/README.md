# trace/

Normalizes runtime-specific execution records into the harness's canonical
trajectory model. Runtime details stop at this package boundary; `core/` and
`evaluators/` consume only `Event` and `Trajectory`.

Modules:

- `model.py` — the normalized trace event / artifact / trajectory records
  (`Event`, `Trajectory`) that `core/` consumes, with JSON save/load.
- `inspect_adapter.py` — Inspect eval log -> normalized `Trajectory`
  (`sample_to_trajectory`, `log_to_trajectories`). Resolves attachment
  placeholders (`resolve_sample_attachments`) before extracting tool-call
  arguments/results, and currently covers the native-tool-loop evidence
  shape used by `tasks/decision_brief.py`.
- `import_recorded.py` — recorded, hand-authored step-list JSON (no Inspect
  involved at all) -> `Trajectory`. Used by the `coding-agent-bugfix`
  scenario's fixtures under `traces/`.
- `import_maf.py` (planned) — Microsoft Agent Framework trace export ->
  normalized `Trajectory`, without requiring MAF at evaluation time.
- `otel_export.py` (not yet implemented) — would export harness results
  *out* to OpenTelemetry / OpenInference-compatible observability tools.

The authoritative adapter boundary and conformance rules live in
[`docs/adapters/`](../../../docs/adapters/index.md).
