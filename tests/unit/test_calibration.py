"""Unit tests for judge calibration: running a registered evaluator
against hand-labeled cases and scoring it, including the repository's
``scenarios/judge-calibration/cases.json`` fixture end-to-end.
"""

from __future__ import annotations

from pathlib import Path

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.core.calibration import run_calibration, run_calibration_file

CASES_FILE = (
    Path(__file__).resolve().parents[2] / "scenarios" / "judge-calibration" / "cases.json"
)


def test_run_calibration_scores_correct_and_incorrect_cases():
    cases = [
        {
            "id": "pass-case",
            "expected_verdict": "PASS",
            "config": {"required_keywords": ["tests"]},
            "bundle": {"final_output": "fixed the bug and added tests"},
        },
        {
            "id": "mismatch-case",
            "expected_verdict": "FAIL",
            "config": {"required_keywords": ["tests"]},
            "bundle": {"final_output": "fixed the bug and added tests"},
        },
    ]
    report = run_calibration("fake_judge", rubric="must mention tests", cases=cases)
    assert report.evaluator_id == "fake_judge"
    assert len(report.results) == 2
    by_id = {r.case_id: r for r in report.results}
    assert by_id["pass-case"].correct is True
    assert by_id["mismatch-case"].correct is False
    assert report.accuracy == 0.5


def test_calibration_report_accuracy_is_zero_with_no_results():
    from agent_eval.core.calibration import CalibrationReport

    assert CalibrationReport(evaluator_id="x").accuracy == 0.0


def test_run_calibration_file_cases_fixture_scores_fully_accurate():
    report = run_calibration_file(CASES_FILE)
    assert report.evaluator_id == "real_judge"
    assert report.accuracy == 1.0
