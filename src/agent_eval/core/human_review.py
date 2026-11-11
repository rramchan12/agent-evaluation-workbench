"""Human review: Stage 3's resolution path for requirements reconciliation
could not already settle on its own (``REVIEW_REQUIRED`` from semantic
disagreement, or ``INSUFFICIENT_EVIDENCE`` from missing/abstained
judgments) -- the third evaluator type in ARCHITECTURE.md §3.2's table,
and the harness's answer to §10's "confidence semantics" question: a human
decision is recorded as an ordinary ``Judgment`` (``kind="human"``) and
always wins reconciliation (see ``core/reconciliation.py``).

This module never calls a model and never touches Inspect AI. It only
takes a ``Report`` the engine already produced, lets something outside the
harness (a person, today) attach a ``HumanDecision`` per flagged
requirement, and reruns reconciliation + release with that decision folded
in -- the same replay-without-rerunning-the-agent guarantee
``agent-eval evaluate`` already gives deterministic/semantic evaluators
(Definition-of-Done item 5) extends to human review too.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_eval.core.engine import Report, RequirementResult
from agent_eval.core.evaluators import Judgment, Verdict
from agent_eval.core.reconciliation import reconcile
from agent_eval.core.release import ReleaseDecision, RequirementOutcome, decide_release

NEEDS_REVIEW_VERDICTS = {"REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE"}


@dataclass
class ReviewItem:
    """One requirement a human reviewer needs to look at."""

    requirement_id: str
    description: str
    importance: str
    verdict: str
    rule_applied: str
    judgments: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "description": self.description,
            "importance": self.importance,
            "verdict": self.verdict,
            "rule_applied": self.rule_applied,
            "judgments": self.judgments,
        }


@dataclass
class HumanDecision:
    """One human reviewer's resolution of one flagged requirement."""

    requirement_id: str
    verdict: Verdict
    reviewer: str
    explanation: str = ""

    @classmethod
    def from_dict(cls, requirement_id: str, data: dict[str, Any]) -> "HumanDecision":
        return cls(
            requirement_id=requirement_id,
            verdict=data["verdict"],
            reviewer=data.get("reviewer", "unknown"),
            explanation=data.get("explanation", ""),
        )


def items_needing_review(report: Report) -> list[ReviewItem]:
    """Every requirement result a human should look at, in report order."""
    return [
        ReviewItem(
            requirement_id=r.requirement.id,
            description=r.requirement.description,
            importance=r.requirement.importance,
            verdict=r.verdict,
            rule_applied=r.rule_applied,
            judgments=[j.to_dict() for j in r.judgments],
        )
        for r in report.requirement_results
        if r.verdict in NEEDS_REVIEW_VERDICTS
    ]


def apply_human_review(report: Report, decisions: list[HumanDecision]) -> Report:
    """Returns a new ``Report`` with each decided requirement's verdict
    resolved by a human judgment (``kind="human"``, which always wins
    reconciliation), and the release decision recomputed from the updated
    requirement verdicts.

    Requirements with no matching decision are left unchanged, including
    ones that still need review -- this function never silently resolves
    something nobody looked at.
    """
    decisions_by_id = {d.requirement_id: d for d in decisions}
    new_results: list[RequirementResult] = []

    for result in report.requirement_results:
        decision = decisions_by_id.get(result.requirement.id)
        if decision is None:
            new_results.append(result)
            continue

        human_judgment = Judgment(
            evaluator_id=decision.reviewer,
            kind="human",
            verdict=decision.verdict,
            explanation=decision.explanation or f"resolved by {decision.reviewer}",
            metadata={"reviewer": decision.reviewer},
        )
        judgments = [*result.judgments, human_judgment]
        reconciled = reconcile(judgments, trajectory_complete=True)
        new_results.append(
            RequirementResult(
                requirement=result.requirement,
                verdict=reconciled.verdict,
                rule_applied=reconciled.rule_applied,
                judgments=judgments,
                evidence_event_ids=result.evidence_event_ids,
            )
        )

    outcomes = [
        RequirementOutcome(
            requirement_id=r.requirement.id,
            importance=r.requirement.importance,
            verdict=r.verdict,
        )
        for r in new_results
    ]
    release_decision: ReleaseDecision = decide_release(outcomes)

    return Report(
        scenario_id=report.scenario_id,
        scenario_name=report.scenario_name,
        trajectory_id=report.trajectory_id,
        system_under_test=report.system_under_test,
        trajectory_sha256=report.trajectory_sha256,
        requirement_results=new_results,
        release_decision=release_decision,
    )
