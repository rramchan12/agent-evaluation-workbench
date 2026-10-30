"""Run tab: pick a scenario + candidate + model, launch a live Inspect AI
evaluation in a background thread, and render the resulting report.

The model field defaults to ``mockllm/model`` (scripted, no network call,
no cost) — the same default ``agent-eval run --model`` uses — so launching
a run never silently calls a paid model.
"""

from __future__ import annotations

import queue

import streamlit as st

from agent_eval.gui import state
from agent_eval.gui.background import start_live_run
from agent_eval.gui.results_view import render_results
from agent_eval.gui.scenario_catalog import discover_scenarios

st.set_page_config(page_title="Run | Agent Evaluation Harness")
state.init_state()

st.header("Run a live evaluation")

scenarios = [s for s in discover_scenarios() if s.inspect_task and s.candidates]
if not scenarios:
    st.warning(
        "No scenario exposes a live-run `metadata.inspect_task` with "
        "candidates yet — use the Replay page instead."
    )
    st.stop()

scenario_by_name = {s.name: s for s in scenarios}
scenario_name = st.selectbox("Scenario", list(scenario_by_name))
scenario_info = scenario_by_name[scenario_name]

candidate_by_name = {c.stem: c for c in scenario_info.candidates}
candidate_name = st.selectbox("Candidate", list(candidate_by_name))
candidate_path = candidate_by_name[candidate_name]

model = st.text_input(
    "Model",
    value="mockllm/model",
    help="Inspect model name. The default is scripted and free -- no network call.",
)

if st.button("Run evaluation", type="primary"):
    state.clear_result()
    thread, progress_queue = start_live_run(
        scenario_path=scenario_info.path,
        task_factory_dotted=scenario_info.inspect_task,
        candidate_path=candidate_path,
        model=model,
    )

    last = None
    with st.status("Running evaluation…", expanded=True) as status:
        while thread.is_alive() or not progress_queue.empty():
            try:
                last = progress_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            status.write(f"stage: {last.stage}")
            if last.stage in ("done", "error"):
                break
        thread.join(timeout=5)

        if last is not None and last.stage == "error":
            status.update(label="Run failed", state="error")
        elif last is not None and last.stage == "done":
            status.update(label="Run complete", state="complete")
        else:
            status.update(label="Run ended without a result", state="error")

    if last is not None and last.stage == "error":
        state.set_error(last.error or "unknown error")
    elif last is not None and last.stage == "done" and last.report and last.trajectory:
        state.set_result(last.report, last.trajectory)
    else:
        state.set_error("The background run ended without a final result or error.")

error = state.get_error()
if error:
    st.error(f"Run failed: {error}")

report = state.get_report()
trajectory = state.get_trajectory()
if report is not None and trajectory is not None:
    render_results(report, trajectory)
