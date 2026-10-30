"""Unit tests for ``agent_eval.gui.trajectory_loader`` — auto-detects a
saved ``Trajectory`` JSON (``"events"`` key) versus a recorded step-list
trace (``"steps"`` key), and loads correctly either way.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_eval.gui.trajectory_loader import trajectory_from_json_text, trajectory_from_path
from agent_eval.trace.model import Trajectory

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACES_DIR = REPO_ROOT / "traces"


def test_trajectory_from_path_loads_step_list_trace():
    trajectory = trajectory_from_path(TRACES_DIR / "coding-bugfix-good.json")

    assert trajectory.scenario_id == "coding-agent-bugfix"
    assert trajectory.events
    assert trajectory.complete is True


def test_trajectory_from_path_loads_insufficient_evidence_trace():
    trajectory = trajectory_from_path(TRACES_DIR / "coding-bugfix-insufficient.json")

    assert trajectory.complete is False
    assert trajectory.incompleteness_reason


def test_trajectory_from_json_text_detects_saved_trajectory_shape():
    saved = Trajectory(
        trajectory_id="t1",
        scenario_id="s1",
        system_under_test="sut",
        events=[],
    )
    text = json.dumps(saved.to_dict())

    loaded = trajectory_from_json_text(text)

    assert loaded.trajectory_id == "t1"
    assert loaded.scenario_id == "s1"
