"""The requirement and scenario model.

Framework-agnostic: nothing here knows that Inspect AI exists. A
``Scenario`` is loaded straight from a JSON file; it declares requirements,
each naming the evaluators (by id) that judge it and the evidence selector
that scopes what those evaluators are allowed to see.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

RequirementKind = Literal["outcome", "obligation", "prohibition", "verification"]
Importance = Literal["blocker", "major", "minor"]


@dataclass
class EvaluatorAssignment:
    """One evaluator assigned to a requirement, by id, with its own config."""

    id: str
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluatorAssignment":
        return cls(id=data["id"], config=data.get("config", {}))


@dataclass
class Requirement:
    """A single, independently evaluated piece of a scenario's task."""

    id: str
    kind: RequirementKind
    description: str
    importance: Importance = "major"
    evidence: dict[str, Any] = field(default_factory=dict)
    """Evidence-selector config: see core/evidence.py."""
    evaluators: list[EvaluatorAssignment] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Requirement":
        return cls(
            id=data["id"],
            kind=data["kind"],
            description=data["description"],
            importance=data.get("importance", "major"),
            evidence=data.get("evidence", {}),
            evaluators=[EvaluatorAssignment.from_dict(e) for e in data.get("evaluators", [])],
        )


@dataclass
class Scenario:
    """A complete, declarative scenario: task identity, requirements, and
    the release policy that turns requirement verdicts into a release
    decision.
    """

    id: str
    name: str
    description: str
    requirements: list[Requirement] = field(default_factory=list)
    release_policy: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def requirement(self, requirement_id: str) -> Requirement | None:
        for r in self.requirements:
            if r.id == requirement_id:
                return r
        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scenario":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            requirements=[Requirement.from_dict(r) for r in data.get("requirements", [])],
            release_policy=data.get("release_policy", {}),
            metadata=data.get("metadata", {}),
        )


def load_scenario(path: str | Path) -> Scenario:
    """Loads a scenario from a ``scenario.json`` file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Scenario.from_dict(data)
