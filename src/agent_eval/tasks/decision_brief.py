"""Inspect AI task definition for the controlled-workspace-decision-brief scenario.

This module is the Inspect-aware boundary for the decision-brief scenario: it
defines the sandboxed workspace tools, builds a scripted ``mockllm`` candidate
from a JSON step-list file, and exposes an Inspect ``@task``. Nothing in
``agent_eval.core`` or ``agent_eval.evaluators`` is imported from here in the
other direction -- this module depends on them, never vice versa.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.solver import generate, use_tools
from inspect_ai.tool import tool
from inspect_ai.util import store

SCENARIO_DIR = (
    Path(__file__).resolve().parents[3] / "scenarios" / "controlled-workspace-decision-brief"
)
WORKSPACE_DIR = SCENARIO_DIR / "workspace"
CANDIDATES_DIR = SCENARIO_DIR / "candidates"

REQUIRED_SECTIONS = [
    "## Executive Summary",
    "## Product Comparison",
    "## Pricing",
    "## Security",
    "## Recommendation",
]


def _load_workspace_docs() -> dict[str, str]:
    """Read every workspace document into a dict keyed by doc id (filename stem)."""
    return {path.stem: path.read_text(encoding="utf-8") for path in sorted(WORKSPACE_DIR.glob("*.md"))}


@tool
def search_workspace():
    """List the ids of documents available in the controlled workspace."""

    async def execute(query: str = "") -> str:
        """List the ids of documents available in the controlled workspace.

        Args:
            query: Optional free-text filter (ignored; all doc ids are returned).

        Returns:
            A newline-separated list of available document ids.
        """
        docs = _load_workspace_docs()
        return "\n".join(f"- {doc_id}" for doc_id in sorted(docs))

    return execute


@tool
def read_artifact():
    """Read the full text of one workspace document by its doc id."""

    async def execute(doc_id: str) -> str:
        """Read the full text of one workspace document.

        Args:
            doc_id: The id of the document to read (see search_workspace).

        Returns:
            The document text, or an error message if the id is unknown.
        """
        docs = _load_workspace_docs()
        if doc_id not in docs:
            return f"error: unknown doc_id '{doc_id}'"
        return docs[doc_id]

    return execute


@tool
def write_artifact():
    """Write (or overwrite) the content of an in-memory artifact at the given path."""

    async def execute(path: str, content: str) -> str:
        """Write (or overwrite) an in-memory artifact.

        Args:
            path: The artifact path to write, e.g. "decision-brief.md".
            content: The full text content to store at that path.

        Returns:
            A short confirmation message.
        """
        artifacts: dict[str, str] = store().get("artifacts", {})
        artifacts[path] = content
        store().set("artifacts", artifacts)
        return f"wrote {len(content)} characters to {path}"

    return execute


@tool
def validate_artifact():
    """Validate that an artifact contains every required decision-brief section."""

    async def execute(path: str) -> dict[str, Any]:
        """Validate that a previously written artifact has every required section.

        Args:
            path: The artifact path to validate, e.g. "decision-brief.md".

        Returns:
            A dict with ``path``, ``valid`` (bool), and ``missing_sections``.
        """
        artifacts: dict[str, str] = store().get("artifacts", {})
        content = artifacts.get(path, "")
        missing = [section for section in REQUIRED_SECTIONS if section not in content]
        return {"path": path, "valid": not missing, "missing_sections": missing}

    return execute


def load_candidate_script(candidate_path: str | Path) -> dict[str, Any]:
    """Load a candidate JSON step-list file (tool calls + final message)."""
    with open(candidate_path, encoding="utf-8") as handle:
        return json.load(handle)


def candidate_outputs(candidate: dict[str, Any]):
    """Build a generator of scripted ``ModelOutput`` values for ``mockllm``.

    Each tool-call step becomes a ``ModelOutput.for_tool_call``; once all
    steps are exhausted, a final plain-text ``ModelOutput.from_content`` ends
    the ``generate(tool_calls='loop')`` loop.
    """

    def _outputs():
        for step in candidate["steps"]:
            yield ModelOutput.for_tool_call(
                model="mockllm",
                tool_name=step["tool"],
                tool_arguments=step["arguments"],
            )
        yield ModelOutput.from_content(
            model="mockllm",
            content=candidate.get("final_message", "Done."),
        )

    return _outputs()


@task
def decision_brief(candidate_path: str | Path) -> Task:
    """Inspect task for a single scripted candidate of the decision-brief scenario."""
    candidate = load_candidate_script(candidate_path)
    model = get_model("mockllm/model", custom_outputs=candidate_outputs(candidate))
    return Task(
        dataset=[
            Sample(
                input=(
                    "Using only the documents available via search_workspace/"
                    "read_artifact, write a decision brief comparing Nimbus Core "
                    "and Nimbus Pro to decision-brief.md following the supplied "
                    "template, then validate it."
                ),
                id=candidate["id"],
            )
        ],
        solver=[
            use_tools(search_workspace(), read_artifact(), write_artifact(), validate_artifact()),
            generate(tool_calls="loop"),
        ],
        model=model,
    )
