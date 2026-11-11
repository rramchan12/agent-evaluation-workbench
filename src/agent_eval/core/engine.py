"""The evaluation engine: wires evidence selection, evaluators, reconciliation
and release policy into one ``evaluate(scenario, trajectory) -> Report`` call.

This is the only function ``cli.py`` needs to call for both the live-run
path (``agent-eval run``) and the evaluator-only replay path
(``agent-eval evaluate``) — it never invokes Inspect AI or any agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agent_eval.core.evaluators import Judgment, run_assignment
from agent_eval.core.evidence import select_evidence
from agent_eval.core.reconciliation import reconcile
from agent_eval.core.release import ReleaseDecision, RequirementOutcome, decide_release
from agent_eval.core.requirements import Requirement, Scenario
from agent_eval.trace.model import Trajectory


@dataclass
class RequirementResult:
    requirement: Requirement
    verdict: str
    rule_applied: str
    judgments: list[Any] = field(default_factory=list)
    evidence_event_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement.id,
            "kind": self.requirement.kind,
            "description": self.requirement.description,
            "importance": self.requirement.importance,
            "verdict": self.verdict,
            "rule_applied": self.rule_applied,
            "judgments": [j.to_dict() for j in self.judgments],
            "evidence_event_ids": self.evidence_event_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementResult":
        """Reconstructs a result from a persisted ``report.json``. The
        rebuilt ``Requirement`` only carries the fields the report itself
        recorded (id/kind/description/importance) -- it never had the
        scenario's ``evidence``/``evaluators`` config to begin with, and
        ``core/human_review.py`` does not need them to resolve a review.
        """
        requirement = Requirement(
            id=data["requirement_id"],
            kind=data["kind"],
            description=data["description"],
            importance=data["importance"],
        )
        return cls(
            requirement=requirement,
            verdict=data["verdict"],
            rule_applied=data["rule_applied"],
            judgments=[Judgment.from_dict(j) for j in data.get("judgments", [])],
            evidence_event_ids=data.get("evidence_event_ids", []),
        )


@dataclass
class Report:
    scenario_id: str
    scenario_name: str
    trajectory_id: str
    system_under_test: str
    trajectory_sha256: str
    requirement_results: list[RequirementResult]
    release_decision: ReleaseDecision
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "trajectory_id": self.trajectory_id,
            "system_under_test": self.system_under_test,
            "trajectory_sha256": self.trajectory_sha256,
            "generated_at": self.generated_at,
            "requirement_results": [r.to_dict() for r in self.requirement_results],
            "release_decision": self.release_decision.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Report":
        """Reconstructs a ``Report`` from a persisted ``report.json`` --
        used by ``agent-eval review`` to load a report, find/apply human
        review, and recompute it without rerunning the agent or evaluators.
        """
        return cls(
            scenario_id=data["scenario_id"],
            scenario_name=data["scenario_name"],
            trajectory_id=data["trajectory_id"],
            system_under_test=data["system_under_test"],
            trajectory_sha256=data["trajectory_sha256"],
            requirement_results=[
                RequirementResult.from_dict(r) for r in data["requirement_results"]
            ],
            release_decision=ReleaseDecision.from_dict(data["release_decision"]),
            generated_at=data.get("generated_at", ""),
        )


def evaluate(scenario: Scenario, trajectory: Trajectory) -> Report:
    results: list[RequirementResult] = []

    for requirement in scenario.requirements:
        bundle = select_evidence(requirement, trajectory)
        judgments = [
            run_assignment(assignment, requirement, bundle)
            for assignment in requirement.evaluators
        ]
        reconciled = reconcile(judgments, trajectory.complete)
        evidence_event_ids = sorted({eid for j in judgments for eid in j.evidence_event_ids})
        results.append(
            RequirementResult(
                requirement=requirement,
                verdict=reconciled.verdict,
                rule_applied=reconciled.rule_applied,
                judgments=judgments,
                evidence_event_ids=evidence_event_ids,
            )
        )

    outcomes = [
        RequirementOutcome(
            requirement_id=r.requirement.id,
            importance=r.requirement.importance,
            verdict=r.verdict,
        )
        for r in results
    ]
    release_decision = decide_release(outcomes, scenario.release_policy)

    return Report(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        trajectory_id=trajectory.trajectory_id,
        system_under_test=trajectory.system_under_test,
        trajectory_sha256=trajectory.sha256(),
        requirement_results=results,
        release_decision=release_decision,
    )
