# reporting/

Renders the reconciled requirement verdicts and release decision into a
portable evidence report.

Implemented in `render.py`:

- JSON report — the canonical, machine-readable result: every requirement's
  verdict, contributing evaluator judgments (with evidence references), and
  the final release decision (see `agent_eval.reporting.render.render_json`).
- Static HTML report — a human-readable rendering of the same data, with
  each verdict's evaluator judgments and evidence listed inline
  (`agent_eval.reporting.render.render_html`).

This is deliberately not a hosted dashboard — see ARCHITECTURE.md's product
boundary. Export to external observability tools (Phoenix, MLflow, etc.) is
a future extension, not part of this package today.
