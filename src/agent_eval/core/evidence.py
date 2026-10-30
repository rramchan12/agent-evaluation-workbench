"""Evidence selection: requirement -> the specific trajectory evidence that
requirement's evaluators are allowed to see.

Evaluators never see the full trajectory. They see an ``EvidenceBundle``,
scoped by the requirement's ``evidence`` selector config:

    {"tool_names": ["read_artifact"], "argument_match": {"doc_id": "unapproved-*"}}

``tool_names`` filters events by ``Event.name``. ``argument_match`` further
filters by glob-matching string argument values. An empty/omitted selector
selects every event — used by requirements whose evaluators only need the
final artifact/output, not specific tool evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any

from agent_eval.core.requirements import Requirement
from agent_eval.trace.model import Event, Trajectory


@dataclass
class EvidenceBundle:
    """The focused slice of a trajectory an evaluator is allowed to see."""

    requirement_id: str
    events: list[Event] = field(default_factory=list)
    trajectory_complete: bool = True
    final_output: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)


def _matches_arg(event: Event, field_name: str, pattern: str) -> bool:
    value = event.arguments.get(field_name)
    if value is None:
        return False
    return fnmatch(str(value), pattern)


def select_evidence(requirement: Requirement, trajectory: Trajectory) -> EvidenceBundle:
    selector = requirement.evidence or {}
    events = trajectory.events

    tool_names = selector.get("tool_names")
    if tool_names:
        events = [e for e in events if e.name in tool_names]

    argument_match = selector.get("argument_match")
    if argument_match:
        events = [
            e for e in events
            if all(_matches_arg(e, field_name, pattern) for field_name, pattern in argument_match.items())
        ]

    return EvidenceBundle(
        requirement_id=requirement.id,
        events=events,
        trajectory_complete=trajectory.complete,
        final_output=trajectory.final_output,
        artifacts=trajectory.artifacts,
    )
