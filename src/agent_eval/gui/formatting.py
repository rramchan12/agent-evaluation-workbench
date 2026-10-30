"""Pure, Streamlit-free helpers turning a ``Report``/``Trajectory`` into
display-ready structures. No ``import streamlit`` here on purpose — this is
what unit tests target without a Streamlit test harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_eval.core.engine import Report
from agent_eval.core.evaluators import Judgment
from agent_eval.reporting.render import _VERDICT_COLOR
from agent_eval.trace.model import Event, Trajectory


def verdict_badge(verdict: str) -> tuple[str, str]:
    """Returns ``(label, color)`` for a verdict, reusing the same color
    table the static HTML report uses (``reporting/render.py``), so the GUI
    and the HTML report always agree on what each verdict looks like."""
    return verdict, _VERDICT_COLOR.get(verdict, "#1f2937")


def has_disagreement(judgments: list[Judgment]) -> bool:
    """True when a requirement's judgments contain more than one distinct
    verdict — evaluators disagreed and it should be visible, not hidden
    behind whatever reconciliation decided."""
    return len({j.verdict for j in judgments}) > 1


@dataclass
class RequirementView:
    """One requirement, with its judgments and disagreement flag, ready to
    render in the shared results view."""

    requirement_id: str
    kind: str
    description: str
    importance: str
    verdict: str
    rule_applied: str
    judgments: list[Judgment] = field(default_factory=list)
    evidence_event_ids: list[str] = field(default_factory=list)
    disagreement: bool = False


def group_by_requirement(report: Report) -> list[RequirementView]:
    """Turns a ``Report``'s requirement results into display-ready views, in
    the same order the scenario declared its requirements."""
    views: list[RequirementView] = []
    for result in report.requirement_results:
        views.append(
            RequirementView(
                requirement_id=result.requirement.id,
                kind=result.requirement.kind,
                description=result.requirement.description,
                importance=result.requirement.importance,
                verdict=result.verdict,
                rule_applied=result.rule_applied,
                judgments=result.judgments,
                evidence_event_ids=result.evidence_event_ids,
                disagreement=has_disagreement(result.judgments),
            )
        )
    return views


def resolve_evidence(trajectory: Trajectory, event_ids: list[str]) -> list[Event]:
    """Resolves evidence event ids to their actual ``Event`` (tool
    name/arguments/result), skipping any id the trajectory does not have."""
    resolved: list[Event] = []
    for event_id in event_ids:
        event = trajectory.event(event_id)
        if event is not None:
            resolved.append(event)
    return resolved
