"""Judge calibration (Stage 3): run a semantic judge against a hand-labeled
cases file and show its accuracy, via ``core.calibration`` -- the same call
``agent-eval calibrate`` makes.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.calibration import run_calibration_file
from agent_eval.gui.formatting import calibration_rows
from agent_eval.gui.scenario_catalog import REPO_ROOT, discover_calibration_files

st.set_page_config(page_title="Calibration | Agent Evaluation Harness")

st.header("Judge calibration")

files = discover_calibration_files()
by_name = {str(p.relative_to(REPO_ROOT)): p for p in files}
upload_option = "(upload a cases JSON)"
choice = st.selectbox("Calibration cases", [*by_name, upload_option])
uploaded = None
if choice == upload_option:
    uploaded = st.file_uploader("Calibration cases JSON", type=["json"])

min_accuracy = st.slider("Minimum accuracy to pass", 0.0, 1.0, 0.8, 0.05)

if st.button("Run calibration", type="primary"):
    try:
        if choice == upload_option:
            if uploaded is None:
                raise ValueError("Upload a cases JSON file first.")
            json.loads(uploaded.getvalue().decode("utf-8"))
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "cases.json"
                path.write_bytes(uploaded.getvalue())
                result = run_calibration_file(path)
        else:
            result = run_calibration_file(by_name[choice])
        st.session_state["gui_calibration"] = (result, min_accuracy)
    except Exception as exc:  # noqa: BLE001
        st.session_state["gui_calibration"] = None
        st.error(f"Could not run calibration: {exc}")

stored = st.session_state.get("gui_calibration")
if stored:
    result, threshold = stored
    ok = result.accuracy >= threshold
    st.metric(f"{result.evaluator_id} accuracy", f"{result.accuracy:.0%}")
    (st.success if ok else st.error)(
        f"{'Meets' if ok else 'Below'} the {threshold:.0%} threshold."
    )
    st.dataframe(calibration_rows(result), use_container_width=True)
