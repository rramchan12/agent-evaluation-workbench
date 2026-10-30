"""Streamlit-free: scenario and trajectory discovery.

Globs ``scenarios/*/scenario.json`` and separately inspects each scenario
folder for a ``candidates/`` directory (live-run capable, needs an Inspect
task) versus none (replay-only). The GUI must never hardcode a scenario id —
new scenarios under ``scenarios/`` show up here automatically.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from agent_eval.core.requirements import load_scenario

REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
TRACES_DIR = REPO_ROOT / "traces"


@dataclass
class ScenarioInfo:
    """One discovered scenario, ready for the Run/Replay forms."""

    id: str
    name: str
    path: Path
    candidates: list[Path] = field(default_factory=list)
    """``scenarios/<id>/candidates/*.json``, empty if the scenario has none."""
    inspect_task: str | None = None
    """``metadata.inspect_task`` dotted path, or ``None`` for replay-only."""


def resolve_task_factory(dotted: str) -> Callable[..., Any]:
    """Resolves ``module.path:function_name`` into a callable Inspect task
    factory. Mirrors ``cli.py``'s ``_resolve_task_factory`` convention
    (duplicated narrowly here, as an 8-line pure function, so the GUI does
    not need to import ``cli.py``)."""
    module_name, _, func_name = dotted.partition(":")
    if not func_name:
        raise ValueError(f"inspect_task must be 'module.path:function_name', got {dotted!r}")
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def discover_scenarios(scenarios_dir: Path = SCENARIOS_DIR) -> list[ScenarioInfo]:
    """Discovers every scenario under ``scenarios_dir`` by loading its
    ``scenario.json``. Order is alphabetical by directory name."""
    infos: list[ScenarioInfo] = []
    for scenario_json in sorted(scenarios_dir.glob("*/scenario.json")):
        scenario = load_scenario(scenario_json)
        candidates_dir = scenario_json.parent / "candidates"
        candidates = sorted(candidates_dir.glob("*.json")) if candidates_dir.is_dir() else []
        infos.append(
            ScenarioInfo(
                id=scenario.id,
                name=scenario.name,
                path=scenario_json,
                candidates=candidates,
                inspect_task=scenario.metadata.get("inspect_task"),
            )
        )
    return infos


def discover_traces(traces_dir: Path = TRACES_DIR, scenario_id: str | None = None) -> list[Path]:
    """Discovers recorded-trace/saved-trajectory JSON files under
    ``traces_dir``, optionally filtered to those whose ``scenario_id`` field
    matches. Files that fail to parse as JSON are silently skipped (an
    upload is the fallback for anything not already a valid fixture)."""
    traces = sorted(traces_dir.glob("*.json")) if traces_dir.is_dir() else []
    if scenario_id is None:
        return traces
    matching: list[Path] = []
    for path in traces:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("scenario_id") == scenario_id:
            matching.append(path)
    return matching
