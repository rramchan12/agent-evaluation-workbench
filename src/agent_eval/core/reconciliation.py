"""Reconciliation: turns a requirement's independent evaluator judgments
into one requirement verdict.

Rules, first match wins (ARCHITECTURE.md §3.4 / §5.6):

1. Incomplete trace, or any evaluator abstained (``INSUFFICIENT_EVIDENCE``):
   -> ``INSUFFICIENT_EVIDENCE``.
2. Any deterministic ``FAIL``: -> ``FAIL`` (deterministic precedence; a
   deterministic FAIL cannot be offset by a passing semantic judge).
3. Semantic judges disagree with each other (and no deterministic FAIL
   applies): -> ``REVIEW_REQUIRED``.
4. Otherwise: -> ``PASS``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_eval.core.evaluators import Judgment, Verdict


@dataclass
class ReconciledVerdict:
    verdict: Verdict
    rule_applied: str
    judgments: list[Judgment] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "rule_applied": self.rule_applied,
            "judgments": [j.to_dict() for j in self.judgments],
        }


def reconcile(judgments: list[Judgment], trajectory_complete: bool) -> ReconciledVerdict:
    if not trajectory_complete or any(j.verdict == "INSUFFICIENT_EVIDENCE" for j in judgments):
        return ReconciledVerdict(
            verdict="INSUFFICIENT_EVIDENCE",
            rule_applied="incomplete_trace_or_abstention",
            judgments=judgments,
        )

    deterministic = [j for j in judgments if j.kind == "deterministic"]
    semantic = [j for j in judgments if j.kind == "semantic"]

    if any(j.verdict == "FAIL" for j in deterministic):
        return ReconciledVerdict(
            verdict="FAIL",
            rule_applied="deterministic_precedence",
            judgments=judgments,
        )

    semantic_verdicts = {j.verdict for j in semantic}
    if len(semantic_verdicts) > 1:
        return ReconciledVerdict(
            verdict="REVIEW_REQUIRED",
            rule_applied="semantic_disagreement",
            judgments=judgments,
        )

    return ReconciledVerdict(
        verdict="PASS",
        rule_applied="all_judgments_pass",
        judgments=judgments,
    )
