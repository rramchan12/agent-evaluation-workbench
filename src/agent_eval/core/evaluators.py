"""The evaluator registry: evaluator id -> implementation.

An evaluator is a plain function ``(requirement, bundle, config) -> Judgment``.
Registering it here is the only thing that makes it usable from a scenario's
``requirements`` — a scenario never introduces new evaluator code, only a
reference by id plus config (see ``evaluators/README.md``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from agent_eval.core.evidence import EvidenceBundle
from agent_eval.core.requirements import EvaluatorAssignment, Requirement

Verdict = Literal["PASS", "FAIL", "REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE"]
EvaluatorKind = Literal["deterministic", "semantic"]


@dataclass
class Judgment:
    """One evaluator's independent verdict on one requirement."""

    evaluator_id: str
    kind: EvaluatorKind
    verdict: Verdict
    explanation: str
    evidence_event_ids: list[str] = field(default_factory=list)
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator_id": self.evaluator_id,
            "kind": self.kind,
            "verdict": self.verdict,
            "explanation": self.explanation,
            "evidence_event_ids": self.evidence_event_ids,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


EvaluatorFn = Callable[[Requirement, EvidenceBundle, dict[str, Any]], Judgment]

_REGISTRY: dict[str, tuple[EvaluatorFn, EvaluatorKind]] = {}


def register(evaluator_id: str, kind: EvaluatorKind) -> Callable[[EvaluatorFn], EvaluatorFn]:
    """Decorator that registers an evaluator function by id."""

    def decorator(fn: EvaluatorFn) -> EvaluatorFn:
        if evaluator_id in _REGISTRY:
            raise ValueError(f"Evaluator id already registered: {evaluator_id}")
        _REGISTRY[evaluator_id] = (fn, kind)
        return fn

    return decorator


def get(evaluator_id: str) -> tuple[EvaluatorFn, EvaluatorKind]:
    if evaluator_id not in _REGISTRY:
        raise KeyError(f"Unknown evaluator id: {evaluator_id}")
    return _REGISTRY[evaluator_id]


def known_evaluator_ids() -> list[str]:
    return sorted(_REGISTRY)


def run_assignment(
    assignment: EvaluatorAssignment, requirement: Requirement, bundle: EvidenceBundle
) -> Judgment:
    fn, kind = get(assignment.id)
    judgment = fn(requirement, bundle, assignment.config)
    judgment.kind = kind
    if not judgment.evaluator_id:
        judgment.evaluator_id = assignment.id
    return judgment
