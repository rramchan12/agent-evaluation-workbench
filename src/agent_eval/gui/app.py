"""Streamlit multipage entry point (``streamlit run src/agent_eval/gui/app.py``).

Streamlit discovers ``pages/1_replay.py``, ``pages/2_review.py`` and ``pages/3_calibration.py`` in this
file's ``pages/`` directory automatically; the numeric prefixes control
sidebar order (Replay, Review, Calibration).
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Agent Evaluation Harness", page_icon="✅", layout="wide")

st.title("Agent Evaluation Harness")
st.markdown(
    "The harness never runs an agent: use the **Replay** page to evaluate a "
    "recorded trace or saved trajectory (ingested through a trace adapter) with "
    "zero agent or model calls. Use **Review** to resolve requirements needing a human "
    "decision, and **Calibration** to measure a judge against labeled "
    "cases. The Replay page renders the release decision / requirement / "
    "evidence report, backed by `agent_eval.core.engine.evaluate` — the "
    "same call the `agent-eval` CLI makes."
)
