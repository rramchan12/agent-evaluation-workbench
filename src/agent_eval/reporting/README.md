# reporting/

Renders the reconciled requirement verdicts and release decision into a
portable evidence report.

Planned modules:

- `json_report.py` — the canonical, machine-readable result: every
  requirement's verdict, contributing evaluator judgments, disagreements,
  evidence references, and the final release decision.
- `html_report.py` — a static, human-readable rendering of the same data,
  with each verdict linking back to its supporting trace events and
  artifacts.

This is deliberately not a hosted dashboard — see ARCHITECTURE.md's product
boundary. Export to external observability tools (Phoenix, MLflow, etc.) is
handled separately, in `trace/otel_export.py`.
