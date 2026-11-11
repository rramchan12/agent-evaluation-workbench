"""The evidence-bounded contract every semantic judge implements, fake or
real (ARCHITECTURE.md §4.3 / §5.5): given a requirement and a specific
evidence bundle -- never the full trajectory -- return a verdict, an
explanation, evidence references, and confidence when that value has a
defined meaning.

``fake_judge`` and ``real_judge`` both depend on this module; it never
depends on either of them, so the shared pieces (text-source resolution,
response parsing) cannot silently drift between the deterministic stand-in
and the real model call that is meant to be swappable with it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from agent_eval.core.evaluators import Judgment
from agent_eval.core.evidence import EvidenceBundle
from agent_eval.core.requirements import Requirement

JUDGE_VERDICTS = {"PASS", "FAIL", "INSUFFICIENT_EVIDENCE"}
"""A single judge never returns REVIEW_REQUIRED -- that verdict only comes
from reconciliation detecting disagreement between judges (or a human
resolving one), never from one judge's own output."""


class Judge(Protocol):
    """Callable contract: ``(requirement, bundle, config) -> Judgment``.

    This is the same shape as ``core.evaluators.EvaluatorFn``, scoped to
    judges specifically so calibration (``core/calibration.py``) can run any
    registered semantic evaluator -- fake or real -- interchangeably.
    """

    def __call__(
        self, requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]
    ) -> Judgment: ...


def text_source(bundle: EvidenceBundle, source: str) -> str | None:
    """Resolves a judge's configured ``text_source`` against an evidence
    bundle: ``"final_output"`` or ``"artifact:<key>"``. Shared by every
    judge so fake and real judges stay comparable in calibration.
    """
    if source == "final_output":
        return bundle.final_output
    if source.startswith("artifact:"):
        key = source.split(":", 1)[1]
        return bundle.artifacts.get(key)
    return None


@dataclass
class ParsedJudgeResponse:
    verdict: str
    explanation: str
    confidence: float | None


def parse_judge_response(raw: str) -> ParsedJudgeResponse:
    """Parses a judge model's raw text response, expected to be a single
    JSON object: ``{"verdict": "PASS"|"FAIL"|"INSUFFICIENT_EVIDENCE",
    "explanation": str, "confidence": float}`` (``confidence`` optional).

    Never raises: an unparseable response, or one with an unrecognized
    verdict, becomes an explicit ``INSUFFICIENT_EVIDENCE`` result rather
    than crashing the evaluation run or silently becoming a pass
    (ARCHITECTURE.md §9 rule 6 -- abstain when evidence, or the judge
    itself, is not reliable).
    """
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return ParsedJudgeResponse(
            verdict="INSUFFICIENT_EVIDENCE",
            explanation=f"judge response was not valid JSON: {raw[:200]!r}",
            confidence=None,
        )

    if not isinstance(data, dict):
        return ParsedJudgeResponse(
            verdict="INSUFFICIENT_EVIDENCE",
            explanation=f"judge response was not a JSON object: {raw[:200]!r}",
            confidence=None,
        )

    verdict = data.get("verdict")
    if verdict not in JUDGE_VERDICTS:
        return ParsedJudgeResponse(
            verdict="INSUFFICIENT_EVIDENCE",
            explanation=f"judge response had an unrecognized verdict: {verdict!r}",
            confidence=None,
        )

    confidence = data.get("confidence")
    if confidence is not None:
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = None

    return ParsedJudgeResponse(
        verdict=verdict,
        explanation=str(data.get("explanation", "")),
        confidence=confidence,
    )
