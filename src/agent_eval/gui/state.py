"""``st.session_state`` keys/helpers shared by the Run and Replay pages: the
last ``Report``/``Trajectory`` (or error) and the background-run handle.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from agent_eval.core.engine import Report
from agent_eval.trace.model import Trajectory

_REPORT_KEY = "gui_report"
_TRAJECTORY_KEY = "gui_trajectory"
_ERROR_KEY = "gui_error"
_THREAD_KEY = "gui_run_thread"
_QUEUE_KEY = "gui_run_queue"


def init_state() -> None:
    """Ensures every key this module manages exists in session state, so
    pages can read before the first write without a ``KeyError``."""
    for key in (_REPORT_KEY, _TRAJECTORY_KEY, _ERROR_KEY, _THREAD_KEY, _QUEUE_KEY):
        if key not in st.session_state:
            st.session_state[key] = None


def set_result(report: Report, trajectory: Trajectory) -> None:
    st.session_state[_REPORT_KEY] = report
    st.session_state[_TRAJECTORY_KEY] = trajectory
    st.session_state[_ERROR_KEY] = None


def set_error(error: str) -> None:
    st.session_state[_ERROR_KEY] = error
    st.session_state[_REPORT_KEY] = None
    st.session_state[_TRAJECTORY_KEY] = None


def clear_result() -> None:
    st.session_state[_REPORT_KEY] = None
    st.session_state[_TRAJECTORY_KEY] = None
    st.session_state[_ERROR_KEY] = None


def get_report() -> Optional[Report]:
    return st.session_state.get(_REPORT_KEY)


def get_trajectory() -> Optional[Trajectory]:
    return st.session_state.get(_TRAJECTORY_KEY)


def get_error() -> Optional[str]:
    return st.session_state.get(_ERROR_KEY)


def set_run_handle(thread, progress_queue) -> None:
    st.session_state[_THREAD_KEY] = thread
    st.session_state[_QUEUE_KEY] = progress_queue


def get_run_handle():
    return st.session_state.get(_THREAD_KEY), st.session_state.get(_QUEUE_KEY)


def clear_run_handle() -> None:
    st.session_state[_THREAD_KEY] = None
    st.session_state[_QUEUE_KEY] = None
