# trace/

Translates between Inspect AI's world and the harness's own trajectory model.
This is the only place that understands Inspect's native eval log format.

Planned modules:

- `inspect_adapter.py` — Inspect eval log -> normalized trajectory. Must
  handle both evidence shapes described in ARCHITECTURE.md: the rich,
  structured tool-call trace produced by a native tool loop, and the
  thinner, message-centric trace produced by a bridged external agent.
- `model.py` — the normalized trace event / artifact / state-change records
  that `core/` consumes.
- `otel_export.py` — exports harness results *out* to OpenTelemetry /
  OpenInference-compatible observability tools. This is an outbound
  capability only — the harness does not depend on an external collector to
  supply input traces.
