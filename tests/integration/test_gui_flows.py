"""Integration tests for the Streamlit GUI (``agent_eval.gui``), using
``streamlit.testing.v1.AppTest`` to drive the Run and Replay pages exactly
as a user would: select widgets, click buttons, assert on rendered output.

No real browser is involved -- ``AppTest`` executes the page script in a
Streamlit "bare mode" runtime and exposes the resulting widget tree.
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from agent_eval.gui.background import start_live_run

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_PAGE = REPO_ROOT / "src" / "agent_eval" / "gui" / "pages" / "1_run.py"
REPLAY_PAGE = REPO_ROOT / "src" / "agent_eval" / "gui" / "pages" / "2_replay.py"


def _markdown_text(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown]


# ---------------------------------------------------------------------------
# Replay page
# ---------------------------------------------------------------------------


def test_replay_pass_fixture_renders_pass_badge():
    at = AppTest.from_file(str(REPLAY_PAGE), default_timeout=30).run()
    at.selectbox[0].set_value("Coding Agent Bugfix").run()
    at.selectbox[1].set_value("coding-bugfix-good").run()
    at.button[0].click().run()

    assert not at.exception
    assert not at.error
    md = _markdown_text(at)
    assert any(">PASS<" in text for text in md)


def test_replay_fail_fixture_renders_fail_badge_and_blocker_requirement():
    at = AppTest.from_file(str(REPLAY_PAGE), default_timeout=30).run()
    at.selectbox[0].set_value("Coding Agent Bugfix").run()
    at.selectbox[1].set_value("coding-bugfix-bad").run()
    at.button[0].click().run()

    assert not at.exception
    md = _markdown_text(at)
    assert any(">FAIL<" in text for text in md)
    assert any("no-test-edits" in exp.label for exp in at.expander)


def test_replay_insufficient_evidence_fixture_renders_that_verdict():
    at = AppTest.from_file(str(REPLAY_PAGE), default_timeout=30).run()
    at.selectbox[0].set_value("Coding Agent Bugfix").run()
    at.selectbox[1].set_value("coding-bugfix-insufficient").run()
    at.button[0].click().run()

    assert not at.exception
    md = _markdown_text(at)
    assert any(">INSUFFICIENT_EVIDENCE<" in text for text in md)
    assert at.info  # incomplete-trajectory banner


def test_replay_without_a_selected_trace_shows_readable_error():
    at = AppTest.from_file(str(REPLAY_PAGE), default_timeout=30).run()
    at.button[0].click().run()

    assert not at.exception
    assert at.error
    assert "Choose a trace" in at.error[0].value


# ---------------------------------------------------------------------------
# Run page
# ---------------------------------------------------------------------------


def test_run_happy_path_candidate_2_passes():
    at = AppTest.from_file(str(RUN_PAGE), default_timeout=60).run()
    at.selectbox[1].set_value("candidate-2").run()
    at.button[0].click().run()

    assert not at.exception
    assert not at.error
    md = _markdown_text(at)
    assert any(">PASS<" in text for text in md)


def test_run_candidate_1_renders_without_crashing():
    at = AppTest.from_file(str(RUN_PAGE), default_timeout=60).run()
    at.button[0].click().run()

    assert not at.exception
    assert not at.error


def test_run_task_error_surfaces_as_error_stage_not_a_crash():
    """The Run page only offers discovered, real candidate files, so a
    "deliberately broken candidate path" cannot be selected through the
    widget tree. Exercise the same ``background.start_live_run`` the page
    calls directly, pointed at a nonexistent candidate path, and confirm
    the background thread reports a readable error instead of raising."""
    scenario_path = (
        REPO_ROOT / "scenarios" / "controlled-workspace-decision-brief" / "scenario.json"
    )
    thread, progress_queue = start_live_run(
        scenario_path=scenario_path,
        task_factory_dotted="agent_eval.tasks.decision_brief:decision_brief",
        candidate_path=REPO_ROOT / "scenarios" / "controlled-workspace-decision-brief"
        / "candidates" / "does-not-exist.json",
    )
    thread.join(timeout=30)

    last = None
    while not progress_queue.empty():
        last = progress_queue.get_nowait()

    assert last is not None
    assert last.stage == "error"
    assert last.error
