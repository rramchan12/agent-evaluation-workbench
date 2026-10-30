"""Renders a ``core.engine.Report`` into a portable evidence report: the
canonical JSON plus a static, human-readable HTML view of the same data.

Deliberately not a hosted dashboard (ARCHITECTURE.md §5.7) — a single
self-contained HTML file with inline styling, no external assets, no
network calls.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from agent_eval.core.engine import Report

_VERDICT_COLOR = {
    "PASS": "#166534",
    "FAIL": "#991b1b",
    "REVIEW_REQUIRED": "#92400e",
    "INSUFFICIENT_EVIDENCE": "#475569",
}


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2, default=str)


def write_json_report(report: Report, path: str | Path) -> None:
    Path(path).write_text(render_json(report), encoding="utf-8")


def _badge(verdict: str) -> str:
    color = _VERDICT_COLOR.get(verdict, "#1f2937")
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-weight:600;font-size:0.85em">{escape(verdict)}</span>'
    )


def _judgment_html(judgment: dict) -> str:
    evidence = ", ".join(judgment.get("evidence_event_ids", [])) or "—"
    confidence = judgment.get("confidence")
    confidence_str = f"{confidence}" if confidence is not None else "—"
    return (
        "<li>"
        f"<strong>{escape(judgment['evaluator_id'])}</strong> "
        f"({escape(judgment['kind'])}) {_badge(judgment['verdict'])}"
        f"<div>{escape(judgment['explanation'])}</div>"
        f"<div><em>evidence:</em> {escape(evidence)} &middot; <em>confidence:</em> {escape(confidence_str)}</div>"
        "</li>"
    )


def _requirement_html(result: dict) -> str:
    judgments_html = "".join(_judgment_html(j) for j in result["judgments"])
    evidence = ", ".join(result.get("evidence_event_ids", [])) or "—"
    return f"""
    <section style="border:1px solid #cbd5e1;border-radius:6px;padding:12px;margin-bottom:12px">
      <h3>{escape(result['requirement_id'])} {_badge(result['verdict'])}</h3>
      <p><em>{escape(result['kind'])} &middot; importance: {escape(result['importance'])} &middot; rule: {escape(result['rule_applied'])}</em></p>
      <p>{escape(result['description'])}</p>
      <p><em>evidence events:</em> {escape(evidence)}</p>
      <ul>{judgments_html}</ul>
    </section>
    """


def render_html(report: Report) -> str:
    data = report.to_dict()
    requirements_html = "".join(_requirement_html(r) for r in data["requirement_results"])
    release = data["release_decision"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Evaluation report: {escape(data['scenario_name'])}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; max-width: 960px; margin: 2rem auto; color: #0f172a; }}
  h1 {{ margin-bottom: 0.2rem; }}
  .meta {{ color: #475569; font-size: 0.9em; }}
  ul {{ padding-left: 1.2rem; }}
</style>
</head>
<body>
  <h1>{escape(data['scenario_name'])}</h1>
  <p class="meta">
    scenario: {escape(data['scenario_id'])} &middot;
    trajectory: {escape(data['trajectory_id'])} &middot;
    system under test: {escape(data['system_under_test'])}<br>
    trajectory sha256: <code>{escape(data['trajectory_sha256'])}</code><br>
    generated at: {escape(data['generated_at'])}
  </p>
  <h2>Release decision: {_badge(release['decision'])}</h2>
  <p class="meta">
    rule: {escape(release['rule_applied'])} &middot;
    contributing requirements: {escape(', '.join(release['contributing_requirements']) or '—')}
  </p>
  <h2>Requirements</h2>
  {requirements_html}
</body>
</html>
"""


def write_html_report(report: Report, path: str | Path) -> None:
    Path(path).write_text(render_html(report), encoding="utf-8")
