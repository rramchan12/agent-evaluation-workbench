"""Shared results view, rendering a ``Report`` the same way for both the
Run and Replay pages: release-decision banner, per-requirement cards
(verdict, importance, kind, description), per-judgment rows, an evidence
expander resolving event ids to the actual ``Event``, and a visible
"evaluators disagreed" flag.
"""

from __future__ import annotations

import streamlit as st

from agent_eval.core.engine import Report
from agent_eval.gui.formatting import group_by_requirement, resolve_evidence, verdict_badge
from agent_eval.trace.model import Trajectory


def _badge_html(verdict: str) -> str:
    label, color = verdict_badge(verdict)
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-weight:600;font-size:0.85em">{label}</span>'
    )


def render_results(report: Report, trajectory: Trajectory) -> None:
    release = report.release_decision

    st.subheader("Release decision")
    st.markdown(_badge_html(release.decision), unsafe_allow_html=True)
    st.caption(
        f"rule: {release.rule_applied} · scenario: {report.scenario_id} · "
        f"trajectory: {report.trajectory_id}"
    )

    if not trajectory.complete:
        st.info(
            "Trajectory marked incomplete: "
            f"{trajectory.incompleteness_reason or 'reason not recorded'}"
        )

    st.subheader("Requirements")
    for view in group_by_requirement(report):
        header = f"{view.requirement_id} — {view.verdict}"
        if view.disagreement:
            header += " ⚠️ evaluators disagreed"
        with st.expander(header, expanded=view.verdict != "PASS"):
            st.markdown(_badge_html(view.verdict), unsafe_allow_html=True)
            st.write(
                f"**{view.kind}** · importance: {view.importance} · "
                f"rule: {view.rule_applied}"
            )
            st.write(view.description)
            if view.disagreement:
                st.warning("Evaluators disagreed on this requirement's verdict.")

            for judgment in view.judgments:
                st.markdown(
                    f"- **{judgment.evaluator_id}** ({judgment.kind}) "
                    f"{_badge_html(judgment.verdict)} — {judgment.explanation}",
                    unsafe_allow_html=True,
                )

            events = resolve_evidence(trajectory, view.evidence_event_ids)
            if events:
                st.write("Evidence:")
                for event in events:
                    st.json(event.to_dict(), expanded=False)
            else:
                st.caption("No evidence events recorded for this requirement.")
