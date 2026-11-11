"""Unit tests for the Stage 3 judge contract and judges: response parsing,
``real_judge`` via scripted ``mock_responses`` (no API key, no network),
and semantic disagreement between ``fake_judge`` and ``real_judge``
producing ``REVIEW_REQUIRED``. No Inspect eval log, no scenario file.
"""

from __future__ import annotations

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.evaluators import run_assignment
from agent_eval.core.evidence import select_evidence
from agent_eval.core.reconciliation import reconcile
from agent_eval.core.requirements import EvaluatorAssignment, Requirement
from agent_eval.evaluators.semantic.judge_interface import parse_judge_response
from agent_eval.trace.model import Trajectory


def make_trajectory(final_output=None, complete=True):
    return Trajectory(
        trajectory_id="t",
        scenario_id="s",
        system_under_test="sut",
        events=[],
        final_output=final_output,
        complete=complete,
    )


def make_requirement(evaluator_id: str, config: dict):
    return Requirement(
        id="r1",
        kind="outcome",
        description="d",
        evaluators=[EvaluatorAssignment(id=evaluator_id, config=config)],
    )


# -- parse_judge_response ----------------------------------------------------


def test_parse_judge_response_valid_json():
    parsed = parse_judge_response('{"verdict": "PASS", "explanation": "ok", "confidence": 0.9}')
    assert parsed.verdict == "PASS"
    assert parsed.explanation == "ok"
    assert parsed.confidence == 0.9


def test_parse_judge_response_invalid_json_is_insufficient_evidence():
    parsed = parse_judge_response("not json")
    assert parsed.verdict == "INSUFFICIENT_EVIDENCE"


def test_parse_judge_response_non_object_json_is_insufficient_evidence():
    parsed = parse_judge_response("[1, 2, 3]")
    assert parsed.verdict == "INSUFFICIENT_EVIDENCE"


def test_parse_judge_response_unrecognized_verdict_is_insufficient_evidence():
    parsed = parse_judge_response('{"verdict": "MAYBE", "explanation": "unsure"}')
    assert parsed.verdict == "INSUFFICIENT_EVIDENCE"
    assert "MAYBE" in parsed.explanation


def test_parse_judge_response_non_numeric_confidence_is_dropped():
    parsed = parse_judge_response('{"verdict": "PASS", "explanation": "ok", "confidence": "high"}')
    assert parsed.verdict == "PASS"
    assert parsed.confidence is None


# -- real_judge ---------------------------------------------------------------


def test_real_judge_pass_from_mock_response():
    requirement = make_requirement(
        "real_judge",
        {
            "rubric": "must mention tests",
            "mock_responses": ['{"verdict": "PASS", "explanation": "tests mentioned", "confidence": 0.9}'],
        },
    )
    bundle = select_evidence(requirement, make_trajectory(final_output="Fixed bug, added tests."))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "PASS"
    assert judgment.kind == "semantic"
    assert judgment.confidence == 0.9


def test_real_judge_fail_from_mock_response():
    requirement = make_requirement(
        "real_judge",
        {
            "rubric": "must mention tests",
            "mock_responses": ['{"verdict": "FAIL", "explanation": "no tests mentioned"}'],
        },
    )
    bundle = select_evidence(requirement, make_trajectory(final_output="Fixed bug."))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "FAIL"


def test_real_judge_abstains_on_incomplete_trajectory_without_calling_model():
    requirement = make_requirement(
        "real_judge",
        {
            "rubric": "must mention tests",
            # If the model were actually called, this would resolve to PASS --
            # proving the abstention happens before any model call.
            "mock_responses": ['{"verdict": "PASS", "explanation": "should not be reached"}'],
        },
    )
    bundle = select_evidence(requirement, make_trajectory(final_output="x", complete=False))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "INSUFFICIENT_EVIDENCE"


def test_real_judge_abstains_below_min_confidence():
    requirement = make_requirement(
        "real_judge",
        {
            "rubric": "must mention tests",
            "min_confidence": 0.7,
            "mock_responses": ['{"verdict": "PASS", "explanation": "probably fine", "confidence": 0.5}'],
        },
    )
    bundle = select_evidence(requirement, make_trajectory(final_output="Fixed bug, maybe tested."))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "INSUFFICIENT_EVIDENCE"
    assert "abstained" in judgment.explanation


def test_real_judge_invalid_model_response_is_insufficient_evidence():
    requirement = make_requirement(
        "real_judge",
        {"rubric": "must mention tests", "mock_responses": ["not json at all"]},
    )
    bundle = select_evidence(requirement, make_trajectory(final_output="Fixed bug."))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "INSUFFICIENT_EVIDENCE"


# -- disagreement between judges ----------------------------------------------


def test_fake_and_real_judge_disagreement_gives_review_required():
    requirement = Requirement(
        id="r1",
        kind="outcome",
        description="d",
        evaluators=[
            EvaluatorAssignment(
                id="fake_judge",
                config={"required_keywords": ["tests"], "text_source": "final_output"},
            ),
            EvaluatorAssignment(
                id="real_judge",
                config={
                    "rubric": "must mention tests",
                    "mock_responses": ['{"verdict": "PASS", "explanation": "looks fine", "confidence": 0.9}'],
                },
            ),
        ],
    )
    trajectory = make_trajectory(final_output="Fixed the bug.")  # no "tests" keyword -> fake_judge FAILs
    bundle = select_evidence(requirement, trajectory)
    judgments = [run_assignment(a, requirement, bundle) for a in requirement.evaluators]
    result = reconcile(judgments, trajectory_complete=True)
    assert result.verdict == "REVIEW_REQUIRED"
    assert result.rule_applied == "semantic_disagreement"
