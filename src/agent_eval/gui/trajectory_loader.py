"""Loads a trajectory from either a saved ``Trajectory`` JSON (produced by
``Trajectory.save``) or a recorded step-list trace JSON (the ``traces/``
fixture shape consumed by ``import_recorded_trace``), distinguished by the
presence of a top-level ``"steps"`` key.

This mirrors ``cli.py``'s ``_load_trajectory`` auto-detection exactly, but is
reimplemented here (not imported from ``cli.py``) so the GUI package does not
depend on the CLI module for an unrelated reason — the same narrow
duplication rationale as ``scenario_catalog.resolve_task_factory``.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_eval.trace.import_recorded import trajectory_from_steps
from agent_eval.trace.model import Trajectory


def trajectory_from_json_text(text: str) -> Trajectory:
    data = json.loads(text)
    if "steps" in data:
        return trajectory_from_steps(data)
    return Trajectory.from_dict(data)


def trajectory_from_path(path: str | Path) -> Trajectory:
    return trajectory_from_json_text(Path(path).read_text(encoding="utf-8"))
