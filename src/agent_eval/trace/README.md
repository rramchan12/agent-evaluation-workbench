# trace/

Translates between Inspect AI's world and the harness's own trajectory model.
This is the only place that understands Inspect's native eval log format.

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
- `otel_export.py` (not yet implemented) — would export harness results
  *out* to OpenTelemetry / OpenInference-compatible observability tools.
