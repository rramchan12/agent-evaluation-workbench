# trace/

The harness's own trajectory model plus importers that produce it.

Modules:

- `model.py` — the normalized trace event / artifact / trajectory records
  (`Event`, `Trajectory`) that `core/` consumes, with JSON save/load.
- `import_recorded.py` — recorded, hand-authored step-list JSON ->
  `Trajectory`. Used by the `coding-agent-bugfix` scenario's fixtures under
  `traces/`.
- `otel_export.py` (not yet implemented) — would export harness results
  *out* to OpenTelemetry / OpenInference-compatible observability tools.

The harness never runs an agent: every trajectory enters through an adapter in
this package, which assigns event ids (`e0`, `e1`, ...) in transcript order.
`import_recorded.py` is the generic adapter; an adapter for an external
runtime's native log (for example Microsoft Agent Framework, ARCHITECTURE.md
Stage 4) would live here too, as another module producing the same
`Trajectory`. (The former `inspect_adapter.py` and the `tasks/` runner were
removed when the harness stopped driving agents.)
