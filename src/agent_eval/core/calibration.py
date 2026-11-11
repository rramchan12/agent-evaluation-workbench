"""Judge calibration: measure a semantic judge's accuracy against a small,
hand-labeled set of evidence bundles with known-correct verdicts, before
trusting that judge in CI (Stage 3, ARCHITECTURE.md §9 rule 6 and §10's
"testing strategy for valid, invalid, and insufficient-evidence
trajectories" -- applied here to judges themselves, not just scenarios).

A calibration case is deliberately *not* a full scenario: it supplies an
evidence bundle directly (final_output / artifacts / events / trajectory
completeness) instead of deriving one from a recorded trajectory, so the
same judge can be checked against PASS, FAIL, and INSUFFICIENT_EVIDENCE
cases without a full agent run backing each one. Any registered semantic
evaluator -- ``fake_judge`` or ``real_judge`` -- can be calibrated this way,
which is what lets a real model judge be checked against the same cases the
fake judge already proved understandable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_eval.core.evaluators import Judgment
from agent_eval.core.evaluators import get as get_evaluator
from agent_eval.core.evidence import EvidenceBundle
from agent_eval.core.requirements import Requirement
from agent_eval.trace.model import Event


@dataclass
class CalibrationResult:
    case_id: str
    expected: str
    actual: str
    judgment: Judgment

    @property
    def correct(self) -> bool:
        return self.expected == self.actual

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "expected": self.expected,
            "actual": self.actual,
            "correct": self.correct,
            "judgment": self.judgment.to_dict(),
        }


@dataclass
class CalibrationReport:
    evaluator_id: str
    results: list[CalibrationResult] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.correct) / len(self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator_id": self.evaluator_id,
            "accuracy": self.accuracy,
            "results": [r.to_dict() for r in self.results],
        }


def _bundle_from_dict(requirement_id: str, data: dict[str, Any]) -> EvidenceBundle:
    events = [Event.from_dict(e) for e in data.get("events", [])]
    return EvidenceBundle(
        requirement_id=requirement_id,
        events=events,
        trajectory_complete=data.get("trajectory_complete", True),
        final_output=data.get("final_output"),
        artifacts=data.get("artifacts", {}),
    )


def run_calibration(
    evaluator_id: str, rubric: str, cases: list[dict[str, Any]]
) -> CalibrationReport:
    """Runs every case through ``evaluator_id`` and scores it against the
    case's ``expected_verdict``. ``rubric`` is the shared default passed to
    every case's config (a case may override it with its own ``config``).
    """
    fn, kind = get_evaluator(evaluator_id)
    results: list[CalibrationResult] = []

    for case in cases:
        requirement = Requirement(
            id=case["id"], kind="outcome", description=case.get("description", rubric)
        )
        bundle = _bundle_from_dict(case["id"], case.get("bundle", {}))
        config = {"rubric": rubric, **case.get("config", {})}

        judgment = fn(requirement, bundle, config)
        judgment.kind = kind
        if not judgment.evaluator_id:
            judgment.evaluator_id = evaluator_id

        results.append(
            CalibrationResult(
                case_id=case["id"],
                expected=case["expected_verdict"],
                actual=judgment.verdict,
                judgment=judgment,
            )
        )

    return CalibrationReport(evaluator_id=evaluator_id, results=results)


def run_calibration_file(path: str | Path) -> CalibrationReport:
    """Loads a calibration cases JSON file: ``{"evaluator_id", "rubric",
    "cases": [{"id", "expected_verdict", "config"?, "bundle"?,
    "description"?}, ...]}`` and runs ``run_calibration`` over it.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return run_calibration(
        evaluator_id=data["evaluator_id"],
        rubric=data.get("rubric", ""),
        cases=data["cases"],
    )
