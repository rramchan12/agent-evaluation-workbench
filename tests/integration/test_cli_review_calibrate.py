"""Integration tests for the ``review`` and ``calibrate`` CLI subcommands:
listing requirements needing review, applying human decisions and
recomputing a report, and scoring a judge against calibration cases --
all driven through ``agent_eval.cli.build_parser()`` like a real invocation.
"""

from __future__ import annotations

import json
from pathlib import Path

import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
from agent_eval.cli import build_parser

REPO_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_CASES = REPO_ROOT / "scenarios" / "judge-calibration" / "cases.json"


def _write_report(path: Path) -> None:
    report = {
        "scenario_id": "s",
        "scenario_name": "S",
        "trajectory_id": "t",
        "system_under_test": "sut",
        "trajectory_sha256": "abc",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "requirement_results": [
            {
                "requirement_id": "r1",
                "kind": "outcome",
                "description": "d",
                "importance": "major",
                "verdict": "REVIEW_REQUIRED",
                "rule_applied": "semantic_disagreement",
                "judgments": [
                    {
                        "evaluator_id": "judge-a",
                        "kind": "semantic",
                        "verdict": "PASS",
                        "explanation": "",
                        "evidence_event_ids": [],
                        "confidence": None,
                        "metadata": {},
                    },
                    {
                        "evaluator_id": "judge-b",
                        "kind": "semantic",
                        "verdict": "FAIL",
                        "explanation": "",
                        "evidence_event_ids": [],
                        "confidence": None,
                        "metadata": {},
                    },
                ],
                "evidence_event_ids": [],
            }
        ],
        "release_decision": {
            "decision": "REVIEW_REQUIRED",
            "rule_applied": "review_required_or_minor_fail",
            "contributing_requirements": ["r1"],
        },
    }
    path.write_text(json.dumps(report), encoding="utf-8")


def test_cli_review_lists_items_needing_review(tmp_path, capsys):
    report_path = tmp_path / "report.json"
    _write_report(report_path)

    parser = build_parser()
    args = parser.parse_args(["review", "--report", str(report_path)])
    exit_code = args.func(args)

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "r1" in out


def test_cli_review_applies_decisions_and_recomputes_release(tmp_path):
    report_path = tmp_path / "report.json"
    _write_report(report_path)

    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(
        json.dumps({"r1": {"verdict": "PASS", "reviewer": "alice"}}), encoding="utf-8"
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "review",
            "--report",
            str(report_path),
            "--decisions",
            str(decisions_path),
            "--out-dir",
            str(tmp_path / "out"),
        ]
    )
    exit_code = args.func(args)

    assert exit_code == 0
    updated = json.loads((tmp_path / "out" / "report.json").read_text(encoding="utf-8"))
    assert updated["requirement_results"][0]["verdict"] == "PASS"
    assert updated["release_decision"]["decision"] == "PASS"


def test_cli_calibrate_scores_fixture_cases(capsys):
    parser = build_parser()
    args = parser.parse_args(["calibrate", "--cases", str(CALIBRATION_CASES)])
    exit_code = args.func(args)

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "accuracy: 1.00" in out


def test_cli_calibrate_nonzero_exit_below_min_accuracy(capsys):
    parser = build_parser()
    args = parser.parse_args(
        ["calibrate", "--cases", str(CALIBRATION_CASES), "--min-accuracy", "1.1"]
    )
    exit_code = args.func(args)
    assert exit_code == 1
