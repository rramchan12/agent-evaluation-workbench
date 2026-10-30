"""Unit tests for reconciliation and the release policy — pure logic over
inline ``Judgment``/``RequirementOutcome`` fixtures, no trajectory needed.
"""

from __future__ import annotations

from agent_eval.core.evaluators import Judgment
from agent_eval.core.reconciliation import reconcile
from agent_eval.core.release import RequirementOutcome, decide_release


def judgment(kind, verdict, evaluator_id="e"):
    return Judgment(evaluator_id=evaluator_id, kind=kind, verdict=verdict, explanation="")


def test_deterministic_fail_overrides_passing_semantic_judge():
    judgments = [
        judgment("deterministic", "FAIL"),
        judgment("semantic", "PASS"),
    ]
    result = reconcile(judgments, trajectory_complete=True)
    assert result.verdict == "FAIL"
    assert result.rule_applied == "deterministic_precedence"


def test_semantic_disagreement_gives_review_required():
    judgments = [
        judgment("semantic", "PASS", "judge-a"),
        judgment("semantic", "FAIL", "judge-b"),
    ]
    result = reconcile(judgments, trajectory_complete=True)
    assert result.verdict == "REVIEW_REQUIRED"
    assert result.rule_applied == "semantic_disagreement"


def test_incomplete_trajectory_gives_insufficient_evidence():
    judgments = [judgment("deterministic", "PASS")]
    result = reconcile(judgments, trajectory_complete=False)
    assert result.verdict == "INSUFFICIENT_EVIDENCE"


def test_abstaining_evaluator_gives_insufficient_evidence_even_if_complete():
    judgments = [judgment("deterministic", "INSUFFICIENT_EVIDENCE")]
    result = reconcile(judgments, trajectory_complete=True)
    assert result.verdict == "INSUFFICIENT_EVIDENCE"


def test_all_pass_gives_pass():
    judgments = [judgment("deterministic", "PASS"), judgment("semantic", "PASS")]
    result = reconcile(judgments, trajectory_complete=True)
    assert result.verdict == "PASS"


def test_release_fails_on_blocker_fail():
    outcomes = [RequirementOutcome("r1", "blocker", "FAIL"), RequirementOutcome("r2", "minor", "PASS")]
    decision = decide_release(outcomes)
    assert decision.decision == "FAIL"
    assert decision.rule_applied == "blocker_or_major_fail"


def test_release_fail_cannot_be_offset_by_other_passes():
    outcomes = [
        RequirementOutcome("quality", "minor", "PASS"),
        RequirementOutcome("policy", "major", "FAIL"),
        RequirementOutcome("verification", "blocker", "PASS"),
    ]
    decision = decide_release(outcomes)
    assert decision.decision == "FAIL"
    assert "policy" in decision.contributing_requirements


def test_release_review_required_when_no_blocking_fail():
    outcomes = [RequirementOutcome("r1", "major", "REVIEW_REQUIRED"), RequirementOutcome("r2", "major", "PASS")]
    decision = decide_release(outcomes)
    assert decision.decision == "REVIEW_REQUIRED"


def test_release_insufficient_evidence_when_no_fail_or_review():
    outcomes = [RequirementOutcome("r1", "major", "INSUFFICIENT_EVIDENCE"), RequirementOutcome("r2", "major", "PASS")]
    decision = decide_release(outcomes)
    assert decision.decision == "INSUFFICIENT_EVIDENCE"


def test_release_pass_when_everything_passes():
    outcomes = [RequirementOutcome("r1", "blocker", "PASS"), RequirementOutcome("r2", "major", "PASS")]
    decision = decide_release(outcomes)
    assert decision.decision == "PASS"
