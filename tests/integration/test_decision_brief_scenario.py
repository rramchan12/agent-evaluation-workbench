"""Integration tests for the controlled-workspace-decision-brief scenario.

These tests exercise the full stack: Inspect AI (via ``mockllm``), the
Inspect log adapter, the scenario file, and the engine -- then separately
prove the evaluator-only replay path (``Trajectory.save``/``.load``)
reproduces identical verdicts with zero further Inspect/model calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.engine import evaluate
from agent_eval.core.requirements import load_scenario
from agent_eval.tasks.decision_brief import decision_brief
from agent_eval.trace.inspect_adapter import eval_log_to_trajectories

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "scenarios" / "controlled-workspace-decision-brief"
SCENARIO_PATH = SCENARIO_DIR / "scenario.json"
CANDIDATES_DIR = SCENARIO_DIR / "candidates"
EXPECTED_DIR = SCENARIO_DIR / "expected"


def _run_candidate(candidate_id: str, tmp_path: Path):
    from inspect_ai import eval as inspect_eval

    scenario = load_scenario(SCENARIO_PATH)
    task = decision_brief(candidate_path=CANDIDATES_DIR / f"{candidate_id}.json")
    logs = inspect_eval(
        task,
        model="mockllm/model",
        log_dir=str(tmp_path / "inspect-logs"),
        display="none",
    )
    log = logs[0]
    assert log.status == "success", log.error
    trajectory = eval_log_to_trajectories(log, scenario_id=scenario.id)[0]
    report = evaluate(scenario, trajectory)
    return scenario, trajectory, report


def _load_expected(candidate_id: str) -> dict:
    return json.loads((EXPECTED_DIR / f"{candidate_id}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("candidate_id", ["candidate-1", "candidate-2"])
def test_candidate_matches_expected_verdicts(candidate_id: str, tmp_path: Path):
    _, _, report = _run_candidate(candidate_id, tmp_path)
    expected = _load_expected(candidate_id)

    assert report.release_decision.decision == expected["release_decision"]
    actual_requirements = {r.requirement.id: r.verdict for r in report.requirement_results}
    assert actual_requirements == expected["requirements"]


@pytest.mark.parametrize("candidate_id", ["candidate-1", "candidate-2"])
def test_replay_from_saved_trajectory_matches_live_run(candidate_id: str, tmp_path: Path):
    scenario, trajectory, live_report = _run_candidate(candidate_id, tmp_path)

    saved_path = tmp_path / "trajectory.json"
    trajectory.save(saved_path)

    # Reload from disk and re-evaluate without touching Inspect or a model.
    from agent_eval.trace.model import Trajectory

    reloaded = Trajectory.load(saved_path)
    replay_report = evaluate(scenario, reloaded)

    assert replay_report.release_decision.decision == live_report.release_decision.decision
    live_verdicts = {r.requirement.id: r.verdict for r in live_report.requirement_results}
    replay_verdicts = {r.requirement.id: r.verdict for r in replay_report.requirement_results}
    assert live_verdicts == replay_verdicts
    assert replay_report.trajectory_sha256 == live_report.trajectory_sha256
