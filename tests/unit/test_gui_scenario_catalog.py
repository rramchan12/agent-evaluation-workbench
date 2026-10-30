"""Unit tests for GUI scenario/trace discovery
(``agent_eval.gui.scenario_catalog``). Runs against the repo's real
``scenarios/`` and ``traces/`` directories so a newly added scenario or
trace file is guaranteed to show up here, not silently invisible to the GUI.
"""

from __future__ import annotations

from agent_eval.gui.scenario_catalog import discover_scenarios, discover_traces


def test_discover_scenarios_finds_both_scenarios_alphabetically():
    infos = discover_scenarios()
    ids = [info.id for info in infos]

    assert "coding-agent-bugfix" in ids
    assert "controlled-workspace-decision-brief" in ids
    # alphabetical by directory name
    assert ids == sorted(ids)


def test_discover_scenarios_inspect_task_only_on_decision_brief():
    infos = {info.id: info for info in discover_scenarios()}

    assert infos["controlled-workspace-decision-brief"].inspect_task == (
        "agent_eval.tasks.decision_brief:decision_brief"
    )
    assert infos["coding-agent-bugfix"].inspect_task is None


def test_discover_scenarios_candidates_populated_when_present():
    infos = {info.id: info for info in discover_scenarios()}

    decision_brief = infos["controlled-workspace-decision-brief"]
    assert len(decision_brief.candidates) >= 1
    assert all(p.suffix == ".json" for p in decision_brief.candidates)


def test_discover_traces_finds_known_fixtures():
    traces = discover_traces()
    names = {p.stem for p in traces}

    assert "coding-bugfix-good" in names
    assert "coding-bugfix-bad" in names
    assert "coding-bugfix-insufficient" in names


def test_discover_traces_filters_by_scenario_id():
    all_traces = discover_traces()
    filtered = discover_traces(scenario_id="coding-agent-bugfix")

    assert filtered, "expected at least one trace for coding-agent-bugfix"
    assert len(filtered) <= len(all_traces)
    assert all(p in all_traces for p in filtered)


def test_discover_traces_empty_for_unknown_scenario_id():
    assert discover_traces(scenario_id="does-not-exist") == []
