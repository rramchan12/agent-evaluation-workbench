"""Integration test for the coding-agent-bugfix scenario: proves the same
generic evaluators/reconciliation/release contracts used by the Inspect-run
decision-brief scenario work unchanged on a purely recorded (non-Inspect)
trajectory (Definition-of-Done item 8).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.engine import evaluate
from agent_eval.core.requirements import load_scenario
from agent_eval.trace.import_recorded import import_recorded_trace

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = REPO_ROOT / "scenarios" / "coding-agent-bugfix" / "scenario.json"
TRACES_DIR = REPO_ROOT / "traces"
EXPECTED_DIR = REPO_ROOT / "expected"


@pytest.mark.parametrize("trace_id", ["coding-bugfix-good", "coding-bugfix-bad"])
def test_recorded_coding_trace_matches_expected_verdicts(trace_id: str):
    scenario = load_scenario(SCENARIO_PATH)
    trajectory = import_recorded_trace(TRACES_DIR / f"{trace_id}.json")
    report = evaluate(scenario, trajectory)

    expected = json.loads((EXPECTED_DIR / f"{trace_id}.json").read_text(encoding="utf-8"))

    assert report.release_decision.decision == expected["release_decision"]
    actual_requirements = {r.requirement.id: r.verdict for r in report.requirement_results}
    assert actual_requirements == expected["requirements"]
