"""Stage 1 semantic evaluator: a deterministic stand-in for a real model
judge, behind the same evidence-bounded contract a real judge will use in
Stage 3. It never calls a model.

A judge is a measuring instrument: every judgment records the judge's id,
its rubric, and the evidence window it was shown, so the fake judge's
reproducibility can later be reused as the acceptance test for a real one.
"""

from __future__ import annotations

from typing import Any

from agent_eval.core.evaluators import Judgment, register
from agent_eval.core.evidence import EvidenceBundle
from agent_eval.core.requirements import Requirement


def _text_source(bundle: EvidenceBundle, source: str) -> str | None:
    if source == "final_output":
        return bundle.final_output
    if source.startswith("artifact:"):
        key = source.split(":", 1)[1]
        return bundle.artifacts.get(key)
    return None


@register("fake_judge", "semantic")
def fake_judge(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """A keyword rubric over bounded evidence text.

    Config:
        judge_id: identity recorded on the judgment (default "fake-judge-v1")
        rubric: human-readable description of what is being judged
        text_source: "final_output" or "artifact:<key>"
        required_keywords: all must appear (case-insensitive) for PASS
        forbidden_keywords: none may appear, else FAIL
    """
    judge_id = config.get("judge_id", "fake-judge-v1")
    rubric = config.get("rubric", "")
    text_source = config.get("text_source", "final_output")

    if not bundle.trajectory_complete:
        return Judgment(
            evaluator_id=judge_id,
            kind="semantic",
            verdict="INSUFFICIENT_EVIDENCE",
            explanation="trajectory is incomplete",
            metadata={"judge_id": judge_id, "rubric": rubric},
        )

    text = _text_source(bundle, text_source) or ""
    lowered = text.lower()

    required_keywords: list[str] = config.get("required_keywords", [])
    forbidden_keywords: list[str] = config.get("forbidden_keywords", [])

    missing = [k for k in required_keywords if k.lower() not in lowered]
    present_forbidden = [k for k in forbidden_keywords if k.lower() in lowered]

    evidence_window = text[:500]
    metadata = {
        "judge_id": judge_id,
        "rubric": rubric,
        "text_source": text_source,
        "evidence_window": evidence_window,
    }

    if present_forbidden:
        return Judgment(
            evaluator_id=judge_id,
            kind="semantic",
            verdict="FAIL",
            explanation=f"Found forbidden content: {', '.join(present_forbidden)}",
            evidence_event_ids=[e.id for e in bundle.events],
            metadata=metadata,
        )
    if missing:
        return Judgment(
            evaluator_id=judge_id,
            kind="semantic",
            verdict="FAIL",
            explanation=f"Missing expected content: {', '.join(missing)}",
            evidence_event_ids=[e.id for e in bundle.events],
            metadata=metadata,
        )
    return Judgment(
        evaluator_id=judge_id,
        kind="semantic",
        verdict="PASS",
        explanation="All rubric criteria satisfied",
        evidence_event_ids=[e.id for e in bundle.events],
        metadata=metadata,
    )
