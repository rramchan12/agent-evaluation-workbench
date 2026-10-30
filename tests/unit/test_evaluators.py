"""Unit tests for evidence selection and the deterministic/semantic
evaluators. No Inspect AI, no scenario file, no recorded trace — only the
module under test and small inline fixtures.
"""

from __future__ import annotations

import pytest

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.evidence import select_evidence
from agent_eval.core.evaluators import run_assignment
from agent_eval.core.requirements import EvaluatorAssignment, Requirement
from agent_eval.trace.model import Event, Trajectory


def make_trajectory(events, final_output=None, artifacts=None, complete=True):
    return Trajectory(
        trajectory_id="t",
        scenario_id="s",
        system_under_test="sut",
        events=events,
        final_output=final_output,
        artifacts=artifacts or {},
        complete=complete,
    )


def test_select_evidence_filters_by_tool_name():
    events = [
        Event(id="e0", kind="tool_call", name="read_artifact", arguments={"doc_id": "a"}),
        Event(id="e1", kind="tool_call", name="write_artifact", arguments={"doc_id": "b"}),
    ]
    requirement = Requirement(
        id="r1", kind="obligation", description="d",
        evidence={"tool_names": ["read_artifact"]},
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    assert [e.id for e in bundle.events] == ["e0"]


def test_select_evidence_filters_by_argument_glob():
    events = [
        Event(id="e0", kind="tool_call", name="read_artifact", arguments={"doc_id": "approved-1"}),
        Event(id="e1", kind="tool_call", name="read_artifact", arguments={"doc_id": "unapproved-1"}),
    ]
    requirement = Requirement(
        id="r1", kind="prohibition", description="d",
        evidence={"tool_names": ["read_artifact"], "argument_match": {"doc_id": "unapproved-*"}},
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    assert [e.id for e in bundle.events] == ["e1"]


def test_required_inspection_fails_when_missing_value():
    events = [Event(id="e0", kind="tool_call", name="read_artifact", arguments={"doc_id": "a"})]
    requirement = Requirement(
        id="r1", kind="obligation", description="d",
        evidence={"tool_names": ["read_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="required_inspection",
            config={"argument_field": "doc_id", "required_values": ["a", "b"]},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "FAIL"
    assert "b" in judgment.explanation


def test_required_inspection_passes_when_all_values_present():
    events = [
        Event(id="e0", kind="tool_call", name="read_artifact", arguments={"doc_id": "a"}),
        Event(id="e1", kind="tool_call", name="read_artifact", arguments={"doc_id": "b"}),
    ]
    requirement = Requirement(
        id="r1", kind="obligation", description="d",
        evidence={"tool_names": ["read_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="required_inspection",
            config={"argument_field": "doc_id", "required_values": ["a", "b"]},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "PASS"


def test_forbidden_access_fails_on_forbidden_value():
    events = [Event(id="e0", kind="tool_call", name="read_artifact", arguments={"doc_id": "unapproved-1"})]
    requirement = Requirement(
        id="r1", kind="prohibition", description="d",
        evidence={"tool_names": ["read_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="forbidden_access",
            config={"argument_field": "doc_id", "forbidden_values": ["unapproved-1"]},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "FAIL"


def test_forbidden_access_passes_when_clean():
    events = [Event(id="e0", kind="tool_call", name="read_artifact", arguments={"doc_id": "approved-1"})]
    requirement = Requirement(
        id="r1", kind="prohibition", description="d",
        evidence={"tool_names": ["read_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="forbidden_access",
            config={"argument_field": "doc_id", "forbidden_values": ["unapproved-1"]},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "PASS"


def test_verify_after_last_write_fails_when_validate_before_write():
    events = [
        Event(id="e0", kind="tool_call", name="validate_artifact", result={"valid": True}),
        Event(id="e1", kind="tool_call", name="write_artifact"),
    ]
    requirement = Requirement(
        id="r1", kind="verification", description="d",
        evidence={"tool_names": ["write_artifact", "validate_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="verify_after_last_write",
            config={"write_tool": "write_artifact", "verify_tool": "validate_artifact", "success_field": "valid"},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "FAIL"


def test_verify_after_last_write_passes_when_validate_after_write():
    events = [
        Event(id="e0", kind="tool_call", name="write_artifact"),
        Event(id="e1", kind="tool_call", name="validate_artifact", result={"valid": True}),
    ]
    requirement = Requirement(
        id="r1", kind="verification", description="d",
        evidence={"tool_names": ["write_artifact", "validate_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="verify_after_last_write",
            config={"write_tool": "write_artifact", "verify_tool": "validate_artifact", "success_field": "valid"},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "PASS"


def test_artifact_sections_detects_missing_section():
    requirement = Requirement(
        id="r1", kind="outcome", description="d",
        evaluators=[EvaluatorAssignment(
            id="artifact_sections",
            config={"artifact_key": "report.md", "required_sections": ["## Summary", "## Recommendation"]},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory([], artifacts={"report.md": "## Summary\ntext"}))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "FAIL"
    assert "Recommendation" in judgment.explanation


def test_citations_observed_fails_on_unobserved_citation():
    events = [Event(id="e0", kind="tool_call", name="read_artifact", arguments={"doc_id": "doc-a"})]
    requirement = Requirement(
        id="r1", kind="prohibition", description="d",
        evidence={"tool_names": ["read_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="citations_observed",
            config={"citation_pattern": r"\[(doc-[\w-]+)\]"},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events, final_output="See [doc-a] and [doc-b]."))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "FAIL"
    assert "doc-b" in judgment.explanation


def test_last_result_matches_checks_last_event_only():
    events = [
        Event(id="e0", kind="tool_call", name="run_tests", result={"all_passed": False}),
        Event(id="e1", kind="tool_call", name="run_tests", result={"all_passed": True}),
    ]
    requirement = Requirement(
        id="r1", kind="outcome", description="d",
        evidence={"tool_names": ["run_tests"]},
        evaluators=[EvaluatorAssignment(
            id="last_result_matches",
            config={"tool_name": "run_tests", "result_field": "all_passed", "equals": True},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory(events))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "PASS"


def test_fake_judge_fails_when_keyword_missing():
    requirement = Requirement(
        id="r1", kind="outcome", description="d",
        evaluators=[EvaluatorAssignment(
            id="fake_judge",
            config={"required_keywords": ["recommendation"], "text_source": "final_output"},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory([], final_output="A plain report."))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "FAIL"
    assert judgment.metadata["judge_id"]


def test_evaluators_abstain_on_incomplete_trajectory():
    requirement = Requirement(
        id="r1", kind="obligation", description="d",
        evidence={"tool_names": ["read_artifact"]},
        evaluators=[EvaluatorAssignment(
            id="required_inspection",
            config={"argument_field": "doc_id", "required_values": ["a"]},
        )],
    )
    bundle = select_evidence(requirement, make_trajectory([], complete=False))
    judgment = run_assignment(requirement.evaluators[0], requirement, bundle)
    assert judgment.verdict == "INSUFFICIENT_EVIDENCE"
