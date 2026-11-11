"""Human review (Stage 3): list the requirements reconciliation could not
settle (``REVIEW_REQUIRED`` / ``INSUFFICIENT_EVIDENCE``), record a reviewer's
verdict per requirement, and recompute the release decision via
``core.human_review.apply_human_review`` -- the same call
``agent-eval review`` makes. No model call, no re-run of the agent.
"""

from __future__ import annotations

import json

import streamlit as st

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.engine import Report
from agent_eval.core.human_review import HumanDecision, apply_human_review, items_needing_review
from agent_eval.gui import state
from agent_eval.gui.formatting import verdict_badge
from agent_eval.gui.results_view import render_results

st.set_page_config(page_title="Review | Agent Evaluation Harness")
state.init_state()

st.header("Human review")

report = state.get_report()
trajectory = state.get_trajectory()

uploaded = st.file_uploader("…or load a saved report.json", type=["json"])
if uploaded is not None and st.button("Load report"):
    try:
        state.set_result(Report.from_dict(json.loads(uploaded.getvalue().decode("utf-8"))), None)
    except Exception as exc:  # noqa: BLE001
        state.set_error(f"Could not load this report: {exc}")
    st.rerun()

error = state.get_error()
if error:
    st.error(error)

if report is None:
    st.info("Run or replay an evaluation first, or load a report.json above.")
    st.stop()

items = items_needing_review(report)
if not items:
    st.success("No requirements need review.")
else:
    st.write(f"{len(items)} requirement(s) need a human decision.")
    reviewer = st.text_input("Reviewer", key="review_reviewer")
    decisions: list[HumanDecision] = []
    with st.form("review_form"):
        entries = []
        for item in items:
            label, color = verdict_badge(item.verdict)
            st.markdown(
                f"**{item.requirement_id}** · importance: {item.importance} · "
                f'<span style="color:{color};font-weight:600">{label}</span>',
                unsafe_allow_html=True,
            )
            st.write(item.description)
            for j in item.judgments:
                conf = j.get("confidence")
                conf_text = f" (confidence {conf:.2f})" if conf is not None else ""
                st.markdown(
                    f"- {j['evaluator_id']} [{j['kind']}] → {j['verdict']}{conf_text}: "
                    f"{j.get('explanation', '')}"
                )
            verdict = st.selectbox(
                "Decision",
                ["(undecided)", "PASS", "FAIL", "INSUFFICIENT_EVIDENCE"],
                key=f"decision_{item.requirement_id}",
            )
            note = st.text_input("Explanation", key=f"note_{item.requirement_id}")
            entries.append((item.requirement_id, verdict, note))
            st.divider()
        submitted = st.form_submit_button("Apply decisions", type="primary")

    if submitted:
        decisions = [
            HumanDecision(rid, verdict, reviewer.strip() or "unknown", note)
            for rid, verdict, note in entries
            if verdict != "(undecided)"
        ]
        if not decisions:
            st.warning("Choose a decision for at least one requirement.")
        else:
            state.set_result(apply_human_review(report, decisions), trajectory)
            st.rerun()

st.divider()
render_results(report, trajectory)
