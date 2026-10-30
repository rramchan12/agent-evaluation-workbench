"""Streamlit multipage entry point (``streamlit run src/agent_eval/gui/app.py``).

Streamlit discovers ``pages/1_run.py`` and ``pages/2_replay.py`` in this
file's ``pages/`` directory automatically; the numeric prefixes control
sidebar order (Run before Replay).
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Agent Evaluation Harness", page_icon="✅", layout="wide")

st.title("Agent Evaluation Harness")
st.markdown(
    "Use the **Run** page to launch a live Inspect AI evaluation, or the "
    "**Replay** page to evaluate a recorded trajectory with zero model "
    "calls. Both pages render the same release decision / requirement / "
    "evidence report, backed by `agent_eval.core.engine.evaluate` — the "
    "same call the `agent-eval` CLI makes."
)
