"""Unit tests for the GUI's Streamlit-free view-model helpers
(``agent_eval.gui.formatting``). No Streamlit import here, no AppTest —
only ``core.engine.evaluate`` against real scenario/trace fixtures plus a
couple of inline ``Judgment`` lists.
"""

from __future__ import annotations

from pathlib import Path

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.engine import evaluate
from agent_eval.core.evaluators import Judgment
from agent_eval.core.requirements import load_scenario
from agent_eval.gui.formatting import (
    group_by_requirement,
    has_disagreement,
    resolve_evidence,
    verdict_badge,
)
from agent_eval.gui.trajectory_loader import trajectory_from_path
from agent_eval.reporting.render import _VERDICT_COLOR
from agent_eval.trace.model import Trajectory

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = REPO_ROOT / "scenarios" / "coding-agent-bugfix" / "scenario.json"
TRACES_DIR = REPO_ROOT / "traces"


def load_trace(name: str) -> Trajectory:
    return trajectory_from_path(TRACES_DIR / name)


def test_verdict_badge_matches_render_color_table():
    for verdict, color in _VERDICT_COLOR.items():
        label, badge_color = verdict_badge(verdict)
        assert label == verdict
        assert badge_color == color


def test_verdict_badge_falls_back_for_unknown_verdict():
    label, color = verdict_badge("SOMETHING_NEW")
    assert label == "SOMETHING_NEW"
    assert color == "#1f2937"


def make_judgment(evaluator_id: str, verdict: str, kind: str = "deterministic") -> Judgment:
    return Judgment(evaluator_id=evaluator_id, kind=kind, verdict=verdict, explanation="")


def test_has_disagreement_true_when_multiple_verdicts():
    judgments = [make_judgment("a", "PASS"), make_judgment("b", "FAIL")]
    assert has_disagreement(judgments) is True


def test_has_disagreement_false_when_same_verdict():
    judgments = [make_judgment("a", "PASS"), make_judgment("b", "PASS")]
    assert has_disagreement(judgments) is False


def test_has_disagreement_false_for_empty_or_single_judgment():
    assert has_disagreement([]) is False
    assert has_disagreement([make_judgment("a", "PASS")]) is False


def test_group_by_requirement_preserves_scenario_order():
    scenario = load_scenario(SCENARIO_PATH)
    trajectory = load_trace("coding-bugfix-good.json")
    report = evaluate(scenario, trajectory)

    views = group_by_requirement(report)

    assert [v.requirement_id for v in views] == [r.id for r in scenario.requirements]
    assert all(v.verdict == "PASS" for v in views)
    assert all(v.disagreement is False for v in views)


def test_group_by_requirement_insufficient_evidence_fixture():
    scenario = load_scenario(SCENARIO_PATH)
    trajectory = load_trace("coding-bugfix-insufficient.json")
    report = evaluate(scenario, trajectory)

    views = group_by_requirement(report)

    assert views, "expected at least one requirement view"
    assert all(v.verdict == "INSUFFICIENT_EVIDENCE" for v in views)
    assert report.release_decision.decision == "INSUFFICIENT_EVIDENCE"


def test_group_by_requirement_fail_fixture():
    scenario = load_scenario(SCENARIO_PATH)
    trajectory = load_trace("coding-bugfix-bad.json")
    report = evaluate(scenario, trajectory)

    views = group_by_requirement(report)

    assert any(v.verdict == "FAIL" for v in views)
    assert report.release_decision.decision == "FAIL"


def test_resolve_evidence_resolves_known_ids_and_skips_unknown():
    trajectory = load_trace("coding-bugfix-good.json")
    known_id = trajectory.events[0].id

    resolved = resolve_evidence(trajectory, [known_id, "not-a-real-id"])

    assert len(resolved) == 1
    assert resolved[0].id == known_id


def test_resolve_evidence_empty_for_no_ids():
    trajectory = load_trace("coding-bugfix-good.json")
    assert resolve_evidence(trajectory, []) == []
