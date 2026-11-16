"""Stage 3 semantic evaluator: a real model judge behind the same
evidence-bounded contract as ``fake_judge`` (``judge_interface.py``).

Like ``fake_judge``, it is config-driven and reusable across scenarios --
the rubric, text source, and model identity all come from the
requirement's evaluator config, never from new code per scenario.

A judge model is a measuring instrument, not part of the system under test
(ARCHITECTURE.md §4.3): it always gets its own model client and its own prompt,
and must never share a model, credential, or session with the agent being
evaluated. Model access goes through `model_client` (stdlib only).
"""

from __future__ import annotations

import os
from typing import Any

from agent_eval.evaluators.semantic.model_client import DEFAULT_MODEL, get_model_client
from agent_eval.core.evaluators import Judgment, register
from agent_eval.core.evidence import EvidenceBundle
from agent_eval.core.requirements import Requirement
from agent_eval.evaluators.semantic.judge_interface import parse_judge_response, text_source

DEFAULT_SYSTEM_PROMPT = (
    "You are an evidence-bounded evaluation judge. You only see the evidence "
    "given to you below, not the full agent trajectory. Respond with a "
    "single JSON object and nothing else: "
    '{"verdict": "PASS"|"FAIL"|"INSUFFICIENT_EVIDENCE", "explanation": '
    '<string>, "confidence": <0.0-1.0>}. Use INSUFFICIENT_EVIDENCE whenever '
    "the evidence does not let you decide either way -- never guess."
)

MODEL_ENV_VAR = "AGENT_EVAL_JUDGE_MODEL"


def _build_prompt(requirement: Requirement, rubric: str, evidence_text: str) -> str:
    return (
        f"Requirement ({requirement.kind}, {requirement.importance}): "
        f"{requirement.description}\n\n"
        f"Rubric: {rubric}\n\n"
        f"Evidence:\n{evidence_text or '(no evidence text available)'}"
    )


def _resolve_model_name(config: dict[str, Any]) -> str:
    return config.get("model") or os.environ.get(MODEL_ENV_VAR, DEFAULT_MODEL)


def _generate(config: dict[str, Any], system_prompt: str, prompt: str) -> str:
    """Builds the judge's model client and runs one synchronous generation.

    `mock_responses` (scripted raw response strings) makes the judge deterministic
    for tests and calibration without any API key -- never set it in production.
    """
    client = get_model_client(_resolve_model_name(config), config.get("mock_responses"))
    return client.generate(system_prompt, prompt)


@register("real_judge", "semantic")
def real_judge(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """A real model-judged evaluator.

    Config:
        judge_id: identity recorded on the judgment (default "real-judge-v1")
        rubric: the question put to the model
        text_source: "final_output" or "artifact:<key>" (default "final_output")
        model: "provider/model" name, e.g. "openai/gpt-4o-mini" (default: $AGENT_EVAL_JUDGE_MODEL, else "mock/model")
        mock_responses: list[str] of scripted raw model responses, for
            deterministic tests/calibration only -- bypasses `model`
        min_confidence: if the model reports confidence below this, abstain
            (downgrade the verdict to INSUFFICIENT_EVIDENCE) rather than
            trust a low-confidence call
        system_prompt: override DEFAULT_SYSTEM_PROMPT
    """
    judge_id = config.get("judge_id", "real-judge-v1")
    rubric = config.get("rubric", "")
    text_source_name = config.get("text_source", "final_output")
    min_confidence = config.get("min_confidence")
    system_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

    if not bundle.trajectory_complete:
        return Judgment(
            evaluator_id=judge_id,
            kind="semantic",
            verdict="INSUFFICIENT_EVIDENCE",
            explanation="trajectory is incomplete",
            metadata={"judge_id": judge_id, "rubric": rubric},
        )

    evidence_text = text_source(bundle, text_source_name) or ""
    prompt = _build_prompt(requirement, rubric, evidence_text)

    raw = _generate(config, system_prompt, prompt)
    parsed = parse_judge_response(raw)

    verdict = parsed.verdict
    explanation = parsed.explanation or f"model returned {verdict} with no explanation"
    if (
        min_confidence is not None
        and parsed.confidence is not None
        and parsed.confidence < min_confidence
    ):
        explanation = (
            f"abstained: confidence {parsed.confidence} below min_confidence "
            f"{min_confidence} (model said {verdict}: {explanation})"
        )
        verdict = "INSUFFICIENT_EVIDENCE"

    return Judgment(
        evaluator_id=judge_id,
        kind="semantic",
        verdict=verdict,
        explanation=explanation,
        evidence_event_ids=[e.id for e in bundle.events],
        confidence=parsed.confidence,
        metadata={
            "judge_id": judge_id,
            "rubric": rubric,
            "text_source": text_source_name,
            "model": "mock_responses" if config.get("mock_responses") else _resolve_model_name(config),
            "evidence_window": evidence_text[:500],
            "raw_response": raw[:1000],
        },
    )
