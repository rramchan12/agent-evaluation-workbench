"""Inspect AI eval log -> normalized ``Trajectory``.

This is the only module that understands Inspect's native log shape. It
assigns sequential event ids (``e0``, ``e1``, ...) in transcript order,
exactly as ``trace/import_recorded.py`` does for non-Inspect traces, so
``core/`` and ``evaluators/`` cannot tell the two apart.

Handles the native tool-loop evidence shape (``ToolEvent`` per call, as
produced by ``generate(tool_calls="loop")`` or ``react()``). A bridged
external agent's thinner, message-centric trace is out of scope for this
slice; see ARCHITECTURE.md §5.3.
"""

from __future__ import annotations

from typing import Any

from inspect_ai.log import EvalLog, EvalSample, resolve_sample_attachments

from agent_eval.trace.model import Event, Trajectory


def _is_tool_event(event: Any) -> bool:
    return getattr(event, "event", None) == "tool"


def sample_to_trajectory(
    sample: EvalSample,
    scenario_id: str,
    system_under_test: str,
    write_tool: str = "write_artifact",
    path_field: str = "path",
    content_field: str = "content",
) -> Trajectory:
    """Normalizes one Inspect ``EvalSample`` into a ``Trajectory``.

    ``write_tool``/``path_field``/``content_field`` tell the adapter which
    tool calls represent artifact writes, so the last write per path becomes
    the final artifact content — this stays generic (no scenario-specific
    logic) because the scenario supplies these names, not this module.
    """
    sample = resolve_sample_attachments(sample, resolve_attachments="full")

    events: list[Event] = []
    artifacts: dict[str, Any] = {}

    for i, raw_event in enumerate(sample.events):
        if not _is_tool_event(raw_event):
            continue
        event_id = f"e{len(events)}"
        arguments = dict(raw_event.arguments or {})
        error = raw_event.error.message if raw_event.error else None
        events.append(
            Event(
                id=event_id,
                kind="tool_call",
                name=raw_event.function,
                arguments=arguments,
                result=raw_event.result,
                error=error,
                timestamp=str(raw_event.timestamp) if getattr(raw_event, "timestamp", None) else None,
                metadata={"tool_call_id": raw_event.id},
            )
        )
        if raw_event.function == write_tool and not raw_event.error:
            path = arguments.get(path_field)
            content = arguments.get(content_field)
            if path is not None:
                artifacts[path] = content

    final_output = sample.output.completion if sample.output else None

    complete = sample.error is None and sample.limit is None
    incompleteness_reason = None
    if sample.error is not None:
        incompleteness_reason = f"sample error: {sample.error.message}"
    elif sample.limit is not None:
        incompleteness_reason = f"sample limit reached: {sample.limit.type}"

    return Trajectory(
        trajectory_id=str(sample.uuid or sample.id),
        scenario_id=scenario_id,
        system_under_test=system_under_test,
        events=events,
        final_output=final_output,
        artifacts=artifacts,
        complete=complete,
        incompleteness_reason=incompleteness_reason,
        metadata={"epoch": sample.epoch},
    )


def eval_log_to_trajectories(
    log: EvalLog,
    scenario_id: str,
    system_under_test: str | None = None,
    **adapter_kwargs: Any,
) -> list[Trajectory]:
    """Normalizes every sample in an eval log into a list of trajectories."""
    sut = system_under_test or (log.eval.model if log.eval else "unknown")
    samples = log.samples or []
    return [
        sample_to_trajectory(sample, scenario_id, sut, **adapter_kwargs)
        for sample in samples
    ]
