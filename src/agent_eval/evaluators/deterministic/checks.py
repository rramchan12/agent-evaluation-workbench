"""Generic, config-driven deterministic evaluators.

None of these functions know about any particular scenario. Each is driven
entirely by the ``config`` dict supplied by the requirement's evaluator
assignment; the same function (e.g. ``forbidden_access``) checks "never read
the unapproved document" in the decision-brief scenario and "never edit
under tests/" in the coding scenario, with zero new code.

Every evaluator here is deterministic: it reaches a verdict purely from the
evidence bundle's event data, with no model call.
"""

from __future__ import annotations

import re
from typing import Any

from agent_eval.core.evaluators import Judgment, register
from agent_eval.core.evidence import EvidenceBundle
from agent_eval.core.requirements import Requirement


def _insufficient(evaluator_id: str, reason: str) -> Judgment:
    return Judgment(
        evaluator_id=evaluator_id,
        kind="deterministic",
        verdict="INSUFFICIENT_EVIDENCE",
        explanation=reason,
    )


@register("required_inspection", "deterministic")
def required_inspection(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """Every value in ``required_values`` must appear as ``argument_field``
    on at least one bundled event (e.g. every required document was read)."""
    if not bundle.trajectory_complete:
        return _insufficient("required_inspection", "trajectory is incomplete")

    argument_field = config["argument_field"]
    required_values = set(config["required_values"])
    observed = {e.arguments.get(argument_field) for e in bundle.events}
    missing = sorted(v for v in required_values if v not in observed)

    if missing:
        return Judgment(
            evaluator_id="required_inspection",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"Missing required inspection of: {', '.join(missing)}",
            evidence_event_ids=[e.id for e in bundle.events],
        )
    return Judgment(
        evaluator_id="required_inspection",
        kind="deterministic",
        verdict="PASS",
        explanation=f"All required values observed: {', '.join(sorted(required_values))}",
        evidence_event_ids=[e.id for e in bundle.events],
    )


@register("forbidden_access", "deterministic")
def forbidden_access(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """No bundled event may carry a forbidden value for ``argument_field``
    (e.g. never read the unapproved document, never edit under tests/)."""
    if not bundle.trajectory_complete:
        return _insufficient("forbidden_access", "trajectory is incomplete")

    argument_field = config["argument_field"]
    forbidden_values = set(config["forbidden_values"])
    violations = [e for e in bundle.events if e.arguments.get(argument_field) in forbidden_values]

    if violations:
        values = ", ".join(sorted({str(e.arguments.get(argument_field)) for e in violations}))
        return Judgment(
            evaluator_id="forbidden_access",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"Forbidden access observed: {values}",
            evidence_event_ids=[e.id for e in violations],
        )
    return Judgment(
        evaluator_id="forbidden_access",
        kind="deterministic",
        verdict="PASS",
        explanation="No forbidden access observed",
        evidence_event_ids=[e.id for e in bundle.events],
    )


@register("verify_after_last_write", "deterministic")
def verify_after_last_write(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """The last ``write_tool`` event must be followed by a successful
    ``verify_tool`` event (e.g. validate after the final write, run tests
    after the final edit)."""
    if not bundle.trajectory_complete:
        return _insufficient("verify_after_last_write", "trajectory is incomplete")

    write_tool = config["write_tool"]
    verify_tool = config["verify_tool"]
    success_field = config.get("success_field", "valid")

    # bundle.events preserves trajectory order, so index position is temporal order.
    write_indices = [i for i, e in enumerate(bundle.events) if e.name == write_tool]
    if not write_indices:
        return Judgment(
            evaluator_id="verify_after_last_write",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"No '{write_tool}' event observed",
        )
    last_write_index = write_indices[-1]

    def is_successful_verify(event) -> bool:
        if event.name != verify_tool:
            return False
        result = event.result
        if isinstance(result, dict):
            return bool(result.get(success_field))
        return bool(result)

    verifications_after = [
        e for e in bundle.events[last_write_index + 1:] if is_successful_verify(e)
    ]

    if verifications_after:
        return Judgment(
            evaluator_id="verify_after_last_write",
            kind="deterministic",
            verdict="PASS",
            explanation=f"'{verify_tool}' succeeded after the last '{write_tool}'",
            evidence_event_ids=[bundle.events[last_write_index].id] + [e.id for e in verifications_after],
        )
    return Judgment(
        evaluator_id="verify_after_last_write",
        kind="deterministic",
        verdict="FAIL",
        explanation=f"No successful '{verify_tool}' observed after the last '{write_tool}'",
        evidence_event_ids=[bundle.events[last_write_index].id],
    )


def _content_for(bundle: EvidenceBundle, artifact_key: str | None) -> str | None:
    if artifact_key:
        return bundle.artifacts.get(artifact_key)
    return bundle.final_output


@register("artifact_sections", "deterministic")
def artifact_sections(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """The final artifact (or final output) must contain every one of
    ``required_sections`` as a substring (e.g. the report template's
    sections were preserved)."""
    if not bundle.trajectory_complete:
        return _insufficient("artifact_sections", "trajectory is incomplete")

    artifact_key = config.get("artifact_key")
    content = _content_for(bundle, artifact_key)
    required_sections: list[str] = config["required_sections"]

    if content is None:
        return Judgment(
            evaluator_id="artifact_sections",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"No artifact content found for key '{artifact_key}'",
        )

    missing = [s for s in required_sections if s not in content]
    if missing:
        return Judgment(
            evaluator_id="artifact_sections",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"Missing required sections: {', '.join(missing)}",
        )
    return Judgment(
        evaluator_id="artifact_sections",
        kind="deterministic",
        verdict="PASS",
        explanation="All required sections present",
    )


@register("citations_observed", "deterministic")
def citations_observed(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """Every reference matched by ``citation_pattern`` in the final artifact
    must correspond to a value actually observed via ``observed_tool`` /
    ``observed_argument_field`` (a citation must point to something read)."""
    if not bundle.trajectory_complete:
        return _insufficient("citations_observed", "trajectory is incomplete")

    artifact_key = config.get("artifact_key")
    content = _content_for(bundle, artifact_key)
    citation_pattern = config["citation_pattern"]
    observed_argument_field = config.get("observed_argument_field", "doc_id")

    if content is None:
        return Judgment(
            evaluator_id="citations_observed",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"No artifact content found for key '{artifact_key}'",
        )

    cited = set(re.findall(citation_pattern, content))
    observed = {e.arguments.get(observed_argument_field) for e in bundle.events}
    unobserved = sorted(c for c in cited if c not in observed)

    if unobserved:
        return Judgment(
            evaluator_id="citations_observed",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"Citations not backed by observed reads: {', '.join(unobserved)}",
        )
    return Judgment(
        evaluator_id="citations_observed",
        kind="deterministic",
        verdict="PASS",
        explanation=f"All {len(cited)} citation(s) backed by observed reads",
    )


@register("last_result_matches", "deterministic")
def last_result_matches(requirement: Requirement, bundle: EvidenceBundle, config: dict[str, Any]) -> Judgment:
    """The most recent bundled event for ``tool_name`` must have a result
    matching the expectation (e.g. the last test run shows all passing)."""
    if not bundle.trajectory_complete:
        return _insufficient("last_result_matches", "trajectory is incomplete")

    tool_name = config["tool_name"]
    result_field = config.get("result_field")
    expected = config.get("equals", True)

    candidates = [e for e in bundle.events if e.name == tool_name]
    if not candidates:
        return Judgment(
            evaluator_id="last_result_matches",
            kind="deterministic",
            verdict="FAIL",
            explanation=f"No '{tool_name}' event observed",
        )
    last = candidates[-1]
    actual = last.result.get(result_field) if (result_field and isinstance(last.result, dict)) else last.result

    if actual == expected:
        return Judgment(
            evaluator_id="last_result_matches",
            kind="deterministic",
            verdict="PASS",
            explanation=f"Last '{tool_name}' result matched expectation ({expected!r})",
            evidence_event_ids=[last.id],
        )
    return Judgment(
        evaluator_id="last_result_matches",
        kind="deterministic",
        verdict="FAIL",
        explanation=f"Last '{tool_name}' result was {actual!r}, expected {expected!r}",
        evidence_event_ids=[last.id],
    )
