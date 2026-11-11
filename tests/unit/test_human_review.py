"""Unit tests for human review: finding requirements that need it, and
resolving them with a human ``Judgment`` that always wins reconciliation
and gets folded into a recomputed release decision.
"""

from __future__ import annotations

from agent_eval.core.engine import RequirementResult
from agent_eval.core.evaluators import Judgment
from agent_eval.core.human_review import HumanDecision, apply_human_review, items_needing_review
from agent_eval.core.reconciliation import reconcile
from agent_eval.core.release import RequirementOutcome, decide_release
from agent_eval.core.requirements import Requirement


def make_report(results):
    from agent_eval.core.engine import Report

    outcomes = [
        RequirementOutcome(r.requirement.id, r.requirement.importance, r.verdict) for r in results
    ]
    return Report(
        scenario_id="s",
        scenario_name="S",
        trajectory_id="t",
        system_under_test="sut",
        trajectory_sha256="abc",
        requirement_results=results,
        release_decision=decide_release(outcomes),
    )


def make_result(requirement_id, verdict, importance="major", judgments=None):
    requirement = Requirement(id=requirement_id, kind="outcome", description="d", importance=importance)
    judgments = judgments or [Judgment(evaluator_id="e", kind="semantic", verdict=verdict, explanation="")]
    reconciled = reconcile(judgments, trajectory_complete=True)
    return RequirementResult(
        requirement=requirement,
        verdict=reconciled.verdict,
        rule_applied=reconciled.rule_applied,
        judgments=judgments,
    )


def test_items_needing_review_includes_review_required_and_insufficient_evidence():
    results = [
        make_result("r1", "PASS"),
        make_result(
            "r2",
            None,
            judgments=[
                Judgment(evaluator_id="a", kind="semantic", verdict="PASS", explanation=""),
                Judgment(evaluator_id="b", kind="semantic", verdict="FAIL", explanation=""),
            ],
        ),
        make_result("r3", "INSUFFICIENT_EVIDENCE"),
    ]
    report = make_report(results)
    items = items_needing_review(report)
    assert {i.requirement_id for i in items} == {"r2", "r3"}


def test_apply_human_review_overrides_review_required_verdict():
    results = [
        make_result(
            "r1",
            None,
            judgments=[
                Judgment(evaluator_id="a", kind="semantic", verdict="PASS", explanation=""),
                Judgment(evaluator_id="b", kind="semantic", verdict="FAIL", explanation=""),
            ],
        ),
    ]
    report = make_report(results)
    assert report.requirement_results[0].verdict == "REVIEW_REQUIRED"

    decision = HumanDecision(requirement_id="r1", verdict="PASS", reviewer="alice")
    updated = apply_human_review(report, [decision])

    r1 = next(r for r in updated.requirement_results if r.requirement.id == "r1")
    assert r1.verdict == "PASS"
    assert r1.rule_applied == "human_resolution"
    assert any(j.kind == "human" and j.evaluator_id == "alice" for j in r1.judgments)
    assert updated.release_decision.decision == "PASS"


def test_apply_human_review_leaves_undecided_requirements_unchanged():
    results = [
        make_result("r1", "INSUFFICIENT_EVIDENCE"),
        make_result("r2", "INSUFFICIENT_EVIDENCE"),
    ]
    report = make_report(results)
    updated = apply_human_review(report, [HumanDecision("r1", "PASS", "alice")])

    r1 = next(r for r in updated.requirement_results if r.requirement.id == "r1")
    r2 = next(r for r in updated.requirement_results if r.requirement.id == "r2")
    assert r1.verdict == "PASS"
    assert r2.verdict == "INSUFFICIENT_EVIDENCE"


def test_human_decision_from_dict():
    decision = HumanDecision.from_dict("r1", {"verdict": "FAIL", "reviewer": "bob", "explanation": "nope"})
    assert decision.requirement_id == "r1"
    assert decision.verdict == "FAIL"
    assert decision.reviewer == "bob"
    assert decision.explanation == "nope"
