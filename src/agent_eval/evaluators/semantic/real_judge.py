"""Stage 3 semantic evaluator: a real model judge behind the same
evidence-bounded contract as ``fake_judge`` (``judge_interface.py``).

Like ``fake_judge``, it is config-driven and reusable across scenarios --
the rubric, text source, and model identity all come from the
requirement's evaluator config, never from new code per scenario.

A judge model is a measuring instrument, not part of the system under test
(ARCHITECTURE.md §4.3): it always gets its own ``get_model(...)`` call and
its own prompt, and must never share a model, credential, or session with
the agent being evaluated.

This module is one of the few places outside ``trace/`` and ``tasks/``
that imports Inspect AI -- it borrows Inspect's model-invocation API
(``inspect_ai.model.get_model``) purely as a model client, not as a task
runner, so the judge still never touches the agent's own execution.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, ModelOutput, get_model

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
DEFAULT_MODEL = "mockllm/model"


def _build_prompt(requirement: Requirement, rubric: str, evidence_text: str) -> str:
    return (
        f"Requirement ({requirement.kind}, {requirement.importance}): "
        f"{requirement.description}\n\n"
        f"Rubric: {rubric}\n\n"
        f"Evidence:\n{evidence_text or '(no evidence text available)'}"
    )


def _resolve_model_name(config: dict[str, Any]) -> str:
    return config.get("model") or os.environ.get(MODEL_ENV_VAR, DEFAULT_MODEL)


def _resolve_model(config: dict[str, Any]):
    """Builds the Inspect model the judge will call.

    ``mock_responses`` (a list of scripted raw response strings) makes the
    judge deterministic for tests and calibration without any API key --
    it must never be set in production configuration. Otherwise, the model
    is named by ``config["model"]``, falling back to the
    ``AGENT_EVAL_JUDGE_MODEL`` environment variable, then ``mockllm/model``.
    """
    mock_responses: list[str] | None = config.get("mock_responses")
    if mock_responses is not None:
        outputs = (
            ModelOutput.from_content(model="mockllm", content=response)
            for response in mock_responses
        )
        return get_model("mockllm/model", custom_outputs=outputs)
    return get_model(_resolve_model_name(config))


def _generate(model, system_prompt: str, prompt: str) -> str:
    """Runs the (async) model call synchronously, matching the plain
    ``(requirement, bundle, config) -> Judgment`` evaluator contract every
    other evaluator -- deterministic or semantic -- already uses.

    Known limitation: this assumes no event loop is already running in the
    calling thread (true for ``core/engine.py``'s current callers: the CLI,
    and tests). Calling ``real_judge`` from inside an already-async context
    would need an async evaluator path, which does not exist yet.
    """
    output: ModelOutput = asyncio.run(
        model.generate(
            input=[
                ChatMessageSystem(content=system_prompt),
                ChatMessageUser(content=prompt),
            ]
        )
    )
    return output.completion


@register("real_judge", "semantic")
def real_judge(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """A real model-judged evaluator.

    Config:
        judge_id: identity recorded on the judgment (default "real-judge-v1")
        rubric: the question put to the model
        text_source: "final_output" or "artifact:<key>" (default "final_output")
        model: Inspect model name (default: $AGENT_EVAL_JUDGE_MODEL, else "mockllm/model")
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

    model = _resolve_model(config)
    raw = _generate(model, system_prompt, prompt)
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
