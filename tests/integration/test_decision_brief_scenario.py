"""Integration tests for the controlled-workspace-decision-brief scenario.

The harness never runs an agent: these tests ingest the recorded traces under
``traces/`` through the trace adapter (``import_recorded_trace``), evaluate
them against the scenario file via the engine, and assert the verdicts match
``scenarios/controlled-workspace-decision-brief/expected/``. They also prove
a saved-and-reloaded ``Trajectory`` reproduces identical verdicts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.engine import evaluate
from agent_eval.core.requirements import load_scenario
from agent_eval.trace.import_recorded import import_recorded_trace
from agent_eval.trace.model import Trajectory

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = REPO_ROOT / "scenarios" / "controlled-workspace-decision-brief"
SCENARIO_PATH = SCENARIO_DIR / "scenario.json"
TRACES_DIR = REPO_ROOT / "traces"
EXPECTED_DIR = SCENARIO_DIR / "expected"


def _evaluate_trace(candidate_id: str):
    scenario = load_scenario(SCENARIO_PATH)
    trajectory = import_recorded_trace(TRACES_DIR / f"decision-brief-{candidate_id}.json")
    assert trajectory.complete, trajectory.incompleteness_reason
    return scenario, trajectory, evaluate(scenario, trajectory)


def _load_expected(candidate_id: str) -> dict:
    return json.loads((EXPECTED_DIR / f"{candidate_id}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("candidate_id", ["candidate-1", "candidate-2"])
def test_trace_matches_expected_verdicts(candidate_id: str):
    _, _, report = _evaluate_trace(candidate_id)
    expected = _load_expected(candidate_id)

    assert report.release_decision.decision == expected["release_decision"]
    actual_requirements = {r.requirement.id: r.verdict for r in report.requirement_results}
    assert actual_requirements == expected["requirements"]


@pytest.mark.parametrize("candidate_id", ["candidate-1", "candidate-2"])
def test_saved_trajectory_replay_matches_first_evaluation(candidate_id: str, tmp_path: Path):
    scenario, trajectory, first_report = _evaluate_trace(candidate_id)

    saved_path = tmp_path / "trajectory.json"
    trajectory.save(saved_path)
    replay_report = evaluate(scenario, Trajectory.load(saved_path))

    assert replay_report.release_decision.decision == first_report.release_decision.decision
    first = {r.requirement.id: r.verdict for r in first_report.requirement_results}
    replay = {r.requirement.id: r.verdict for r in replay_report.requirement_results}
    assert first == replay
    assert replay_report.trajectory_sha256 == first_report.trajectory_sha256
