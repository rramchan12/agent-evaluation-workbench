"""Imports a hand-authored or externally recorded trace into a ``Trajectory``.

This is the path used for scenarios that do not run through Inspect AI at
all (Stage 2's coding-agent trace). The input is plain JSON: a flat,
ordered list of steps. This importer assigns sequential event ids
(``e0``, ``e1``, ...) exactly as ``inspect_adapter.py`` does, so evidence
selectors and evaluators cannot tell which source produced a trajectory.

Recorded-trace JSON shape::

    {
      "trajectory_id": "...",
      "scenario_id": "...",
      "system_under_test": "...",
      "final_output": "...",
      "artifacts": {"path/to/file": "contents", ...},
      "complete": true,
      "steps": [
        {"kind": "tool_call", "name": "read_file", "arguments": {...},
         "result": ..., "timestamp": "...", "metadata": {...}},
        ...
      ]
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_eval.trace.model import Event, Trajectory


def import_recorded_trace(path: str | Path) -> Trajectory:
    """Loads a recorded step-list JSON file and normalizes it to a Trajectory."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return trajectory_from_steps(data)


def trajectory_from_steps(data: dict[str, Any]) -> Trajectory:
    events: list[Event] = []
    for i, step in enumerate(data.get("steps", [])):
        events.append(
            Event(
                id=f"e{i}",
                kind=step.get("kind", "tool_call"),
                name=step.get("name"),
                arguments=step.get("arguments", {}) or {},
                result=step.get("result"),
                error=step.get("error"),
                timestamp=step.get("timestamp"),
                metadata=step.get("metadata", {}) or {},
            )
        )

    return Trajectory(
        trajectory_id=data["trajectory_id"],
        scenario_id=data["scenario_id"],
        system_under_test=data.get("system_under_test", "recorded"),
        events=events,
        final_output=data.get("final_output"),
        artifacts=data.get("artifacts", {}),
        complete=data.get("complete", True),
        incompleteness_reason=data.get("incompleteness_reason"),
        metadata=data.get("metadata", {}),
    )
