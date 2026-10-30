"""The release policy engine: requirement verdicts -> one release decision.

Order, first match wins (ARCHITECTURE.md §3.4):

1. A ``FAIL`` on a ``blocker`` or ``major`` requirement fails the release
   outright — quality elsewhere cannot offset it.
2. Otherwise, any requirement at ``REVIEW_REQUIRED`` (including a ``FAIL``
   on a ``minor`` requirement, which cannot fail the release by itself but
   must not be silently dropped) makes the release ``REVIEW_REQUIRED``.
3. Otherwise, any requirement at ``INSUFFICIENT_EVIDENCE`` makes the release
   ``INSUFFICIENT_EVIDENCE``.
4. Otherwise ``PASS``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_eval.core.evaluators import Verdict
from agent_eval.core.requirements import Importance


@dataclass
class RequirementOutcome:
    requirement_id: str
    importance: Importance
    verdict: Verdict


@dataclass
class ReleaseDecision:
    decision: Verdict
    rule_applied: str
    contributing_requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "rule_applied": self.rule_applied,
            "contributing_requirements": self.contributing_requirements,
        }


def decide_release(outcomes: list[RequirementOutcome], release_policy: dict[str, Any] | None = None) -> ReleaseDecision:
    blocking_fail = [
        o for o in outcomes if o.verdict == "FAIL" and o.importance in ("blocker", "major")
    ]
    if blocking_fail:
        return ReleaseDecision(
            decision="FAIL",
            rule_applied="blocker_or_major_fail",
            contributing_requirements=[o.requirement_id for o in blocking_fail],
        )

    review_required = [
        o for o in outcomes
        if o.verdict == "REVIEW_REQUIRED" or (o.verdict == "FAIL" and o.importance == "minor")
    ]
    if review_required:
        return ReleaseDecision(
            decision="REVIEW_REQUIRED",
            rule_applied="review_required_or_minor_fail",
            contributing_requirements=[o.requirement_id for o in review_required],
        )

    insufficient = [o for o in outcomes if o.verdict == "INSUFFICIENT_EVIDENCE"]
    if insufficient:
        return ReleaseDecision(
            decision="INSUFFICIENT_EVIDENCE",
            rule_applied="insufficient_evidence",
            contributing_requirements=[o.requirement_id for o in insufficient],
        )

    return ReleaseDecision(
        decision="PASS",
        rule_applied="all_requirements_pass",
        contributing_requirements=[o.requirement_id for o in outcomes],
    )
