"""Normalized trace model shared by every other layer in this package.

``Event`` and ``Trajectory`` are the one shape that ``core/`` and
``evaluators/`` understand. They know nothing about Inspect AI; this module
itself has no Inspect AI dependency either, so trajectories produced here can
come from a live Inspect run (``trace/inspect_adapter.py``), a hand-authored
recorded trace (``trace/import_recorded.py``), or any future importer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Event:
    """A single, addressable step in a trajectory.

    Event ids are assigned sequentially (``e0``, ``e1``, ...) by whatever
    produced the trajectory, and are the unit evidence selectors and
    evaluators reference when pointing back at what they saw.
    """

    id: str
    kind: str
    """e.g. "tool_call", "message", "score"."""

    name: Optional[str] = None
    """Tool/function name, when applicable."""

    arguments: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Trajectory:
    """A complete, evidence-addressable record of one agent run.

    ``complete`` is set to ``False`` by an importer when it knows the source
    data was truncated or an error aborted the run before it could capture
    everything (e.g. a sample limit, a crash, a partial log) — this is the
    signal ``core/reconciliation.py`` uses to produce
    ``INSUFFICIENT_EVIDENCE`` instead of silently treating missing evidence
    as a pass.
    """

    trajectory_id: str
    scenario_id: str
    system_under_test: str
    """Identity of the agent/model/config that produced this trajectory."""

    events: list[Event] = field(default_factory=list)
    final_output: Optional[str] = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    """Final named artifact contents, e.g. {"report.md": "..."}."""

    complete: bool = True
    incompleteness_reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def event(self, event_id: str) -> Optional[Event]:
        for e in self.events:
            if e.id == event_id:
                return e
        return None

    def events_by_kind(self, kind: str) -> list[Event]:
        return [e for e in self.events if e.kind == kind]

    def events_by_name(self, name: str) -> list[Event]:
        return [e for e in self.events if e.name == name]

    def sha256(self) -> str:
        """Content hash of the trajectory, used as provenance in reports."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "scenario_id": self.scenario_id,
            "system_under_test": self.system_under_test,
            "events": [e.to_dict() for e in self.events],
            "final_output": self.final_output,
            "artifacts": self.artifacts,
            "complete": self.complete,
            "incompleteness_reason": self.incompleteness_reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trajectory":
        events = [Event.from_dict(e) for e in data.get("events", [])]
        return cls(
            trajectory_id=data["trajectory_id"],
            scenario_id=data["scenario_id"],
            system_under_test=data["system_under_test"],
            events=events,
            final_output=data.get("final_output"),
            artifacts=data.get("artifacts", {}),
            complete=data.get("complete", True),
            incompleteness_reason=data.get("incompleteness_reason"),
            metadata=data.get("metadata", {}),
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str | Path) -> "Trajectory":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)
