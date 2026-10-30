"""Replay tab: pick a scenario and either an existing trace/trajectory
fixture or an uploaded JSON file, evaluate it directly against
``core.engine.evaluate`` -- no Inspect AI, no model call -- and render the
same results view the Run tab uses.
"""

from __future__ import annotations

import streamlit as st

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.engine import evaluate as run_engine
from agent_eval.core.requirements import load_scenario
from agent_eval.gui import state
from agent_eval.gui.results_view import render_results
from agent_eval.gui.scenario_catalog import discover_scenarios, discover_traces
from agent_eval.gui.trajectory_loader import trajectory_from_json_text, trajectory_from_path

st.set_page_config(page_title="Replay | Agent Evaluation Harness")
state.init_state()

st.header("Replay a recorded trajectory")

scenarios = discover_scenarios()
if not scenarios:
    st.warning("No scenario found under `scenarios/`.")
    st.stop()

scenario_by_name = {s.name: s for s in scenarios}
scenario_name = st.selectbox("Scenario", list(scenario_by_name))
scenario_info = scenario_by_name[scenario_name]

traces = discover_traces(scenario_id=scenario_info.id)
trace_by_name = {t.stem: t for t in traces}
upload_option = "(upload a trajectory/trace JSON)"
source_choice = st.selectbox("Trajectory source", [upload_option, *trace_by_name])

uploaded_file = None
if source_choice == upload_option:
    uploaded_file = st.file_uploader(
        "Saved Trajectory JSON or recorded step-list trace JSON", type=["json"]
    )

if st.button("Evaluate", type="primary"):
    state.clear_result()
    try:
        scenario = load_scenario(scenario_info.path)
        if source_choice == upload_option:
            if uploaded_file is None:
                raise ValueError(
                    "Choose a trace from the dropdown, or upload a JSON file first."
                )
            trajectory = trajectory_from_json_text(uploaded_file.getvalue().decode("utf-8"))
        else:
            trajectory = trajectory_from_path(trace_by_name[source_choice])
        report = run_engine(scenario, trajectory)
        state.set_result(report, trajectory)
    except Exception as exc:  # noqa: BLE001 - show a readable message, never an uncaught traceback
        state.set_error(f"Could not evaluate this trajectory: {exc}")

error = state.get_error()
if error:
    st.error(error)

report = state.get_report()
trajectory = state.get_trajectory()
if report is not None and trajectory is not None:
    render_results(report, trajectory)
