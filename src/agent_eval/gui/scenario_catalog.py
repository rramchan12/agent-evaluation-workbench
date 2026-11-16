"""Streamlit-free: scenario and trajectory discovery.

Globs ``scenarios/*/scenario.json`` and ``traces/*.json``. The GUI must never
hardcode a scenario id — new scenarios under ``scenarios/`` show up here
automatically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agent_eval.core.requirements import load_scenario

REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
TRACES_DIR = REPO_ROOT / "traces"


@dataclass
class ScenarioInfo:
    """One discovered scenario, ready for the Replay form."""

    id: str
    name: str
    path: Path


def discover_scenarios(scenarios_dir: Path = SCENARIOS_DIR) -> list[ScenarioInfo]:
    """Discovers every scenario under ``scenarios_dir`` by loading its
    ``scenario.json``. Order is alphabetical by directory name."""
    infos: list[ScenarioInfo] = []
    for scenario_json in sorted(scenarios_dir.glob("*/scenario.json")):
        scenario = load_scenario(scenario_json)
        infos.append(
            ScenarioInfo(
                id=scenario.id,
                name=scenario.name,
                path=scenario_json,
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


def discover_calibration_files(scenarios_dir: Path = SCENARIOS_DIR) -> list[Path]:
    """Every ``scenarios/*/cases.json`` calibration file (Stage 3)."""
    return sorted(scenarios_dir.glob("*/cases.json"))
