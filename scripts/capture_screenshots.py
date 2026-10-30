"""One-off, manual screenshot-capture helper for the GUI README.

Starts ``streamlit run src/agent_eval/gui/app.py`` as a subprocess, drives it
with Playwright (headless Chromium), and writes 2 PNGs into
``docs/screenshots/``:

- ``run-complete-pass.png``: Run tab, decision-brief scenario, candidate-2
  (passes cleanly), after the live mockllm run completes.
- ``replay-fail-disagreement.png``: Replay tab, decision-brief scenario, an
  uploaded trajectory from candidate-1 (fails, and its
  ``approved-sources-only`` requirement shows evaluator disagreement -- the
  deterministic ``forbidden_access`` evaluator says FAIL while the semantic
  ``grounding-judge-v1`` says PASS).

This script is **not** part of ``pytest``/CI -- it needs Playwright's
Chromium browser installed (``pip install playwright && playwright install
chromium``) and is meant to be re-run by hand whenever the GUI's look
changes enough to make the README screenshots stale.

Usage::

    pip install playwright
    playwright install chromium
    python scripts/capture_screenshots.py
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "screenshots"
APP_PATH = REPO_ROOT / "src" / "agent_eval" / "gui" / "app.py"


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with closing(socket.create_connection(("127.0.0.1", port), timeout=1)):
                return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Streamlit server did not come up on port {port} in time")


def _make_candidate1_trajectory_json(tmp_dir: Path) -> Path:
    """Runs candidate-1 through Inspect AI (mockllm, free) once, and saves
    the resulting trajectory as plain JSON -- this is what a user would
    upload to the Replay tab. Not committed; written to a temp dir and
    cleaned up after the screenshot is taken."""
    import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
    from inspect_ai import eval as inspect_eval

    from agent_eval.core.requirements import load_scenario
    from agent_eval.tasks.decision_brief import decision_brief
    from agent_eval.trace.inspect_adapter import eval_log_to_trajectories

    scenario_dir = REPO_ROOT / "scenarios" / "controlled-workspace-decision-brief"
    scenario = load_scenario(scenario_dir / "scenario.json")
    task = decision_brief(candidate_path=scenario_dir / "candidates" / "candidate-1.json")
    logs = inspect_eval(
        task, model="mockllm/model", log_dir=str(tmp_dir / "inspect-logs"), display="none"
    )
    trajectory = eval_log_to_trajectories(logs[0], scenario_id=scenario.id)[0]
    out_path = tmp_dir / "candidate-1-trajectory.json"
    trajectory.save(out_path)
    return out_path


def _select_streamlit_option(page, label: str, option_text: str) -> None:
    """Streamlit's ``st.selectbox`` renders a BaseWeb combobox, not a plain
    HTML ``<select>`` -- ``select_option`` does not apply. Click it open,
    then click the matching option in the listbox that pops up."""
    widget = page.locator('[data-testid="stSelectbox"]', has_text=label).locator(
        '[role="combobox"]'
    )
    widget.click()
    page.get_by_role("option", name=option_text, exact=True).click()


def _screenshot_fitted(page, path: Path) -> None:
    """Resizes the viewport to the main content's actual rendered height
    (Streamlit's content area scrolls inside a nested div, so a fixed
    viewport either clips content or leaves a lot of blank space below
    it) then takes a plain (non full-page) screenshot."""
    height = page.evaluate(
        "() => {"
        "  const el = document.querySelector('[data-testid=\"stMain\"]')"
        "    || document.querySelector('.main')"
        "    || document.querySelector('[data-testid=\"stAppViewContainer\"]');"
        "  return el ? el.scrollHeight : document.body.scrollHeight;"
        "}"
    )
    page.set_viewport_size({"width": 1280, "height": min(max(height, 600), 4000)})
    page.wait_for_timeout(200)
    page.screenshot(path=str(path))


def main() -> None:
    from playwright.sync_api import sync_playwright

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    tmp_handle = TemporaryDirectory()
    tmp_dir = Path(tmp_handle.name)
    # Computed before Playwright starts: Inspect AI's own asyncio runner and
    # Playwright's sync API cannot share a thread/event loop.
    trajectory_path = _make_candidate1_trajectory_json(tmp_dir)

    port = _free_port()
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_PATH),
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(REPO_ROOT),
    )
    try:
        _wait_for_server(port)
        base_url = f"http://127.0.0.1:{port}"

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            # --- Run tab: decision-brief + candidate-2, clean PASS ---
            page.goto(base_url, wait_until="networkidle")
            page.get_by_role("link", name="run").click()
            page.wait_for_load_state("networkidle")
            _select_streamlit_option(page, "Candidate", "candidate-2")
            page.get_by_role("button", name="Run evaluation").click()
            page.get_by_text("Run complete").wait_for(timeout=30_000)
            page.get_by_text("validate-after-last-write").wait_for(timeout=20_000)
            page.wait_for_timeout(1000)
            _screenshot_fitted(page, SCREENSHOTS_DIR / "run-complete-pass.png")

            # --- Replay tab: decision-brief + candidate-1, FAIL + disagreement ---
            page.goto(base_url, wait_until="networkidle")
            page.get_by_role("link", name="replay").click()
            page.wait_for_load_state("networkidle")
            _select_streamlit_option(
                page, "Scenario", "Controlled Workspace Decision Brief"
            )
            page.locator('[data-testid="stFileUploaderDropzoneInput"]').set_input_files(
                str(trajectory_path)
            )
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Evaluate").click()
            page.get_by_text("Release decision").wait_for(timeout=15_000)
            page.get_by_text("validate-after-last-write").wait_for(timeout=15_000)
            page.wait_for_timeout(1000)
            _screenshot_fitted(page, SCREENSHOTS_DIR / "replay-fail-disagreement.png")

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        tmp_handle.cleanup()

    print(f"Wrote screenshots to {SCREENSHOTS_DIR}")


if __name__ == "__main__":
    main()

