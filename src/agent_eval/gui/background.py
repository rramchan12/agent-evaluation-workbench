"""Thread-based runner for the Run tab's live-run path.

Streamlit blocks the main thread on a long-running call and reruns the
whole script on every interaction, so an Inspect AI run must happen off the
main thread. This wraps the exact same call sequence ``cli.cmd_run`` makes
(``load_scenario`` -> resolve task factory -> ``inspect_eval`` ->
``eval_log_to_trajectories`` -> ``core.engine.evaluate``), pushing a
``RunProgress`` onto a thread-safe queue before/after each stage, and
catching every exception so a crash becomes a ``stage="error"`` item instead
of an unhandled exception in a background thread (which Streamlit/the user
would never see).
"""

from __future__ import annotations

import queue
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from agent_eval.core.engine import Report
from agent_eval.core.engine import evaluate as run_engine
from agent_eval.core.requirements import load_scenario
from agent_eval.gui.scenario_catalog import resolve_task_factory
from agent_eval.trace.model import Trajectory


@dataclass
class RunProgress:
    """One update pushed onto the progress queue."""

    stage: str
    """"starting" | "running" | "evaluating" | "done" | "error"."""

    report: Optional[Report] = None
    trajectory: Optional[Trajectory] = None
    error: Optional[str] = None
    """Short, user-facing error message."""

    detail: Optional[str] = None
    """Full traceback, for an optional "show details" expander."""


def start_live_run(
    scenario_path: str | Path,
    task_factory_dotted: str,
    candidate_path: str | Path,
    model: str = "mockllm/model",
    log_dir: str | Path = "inspect-logs",
) -> "tuple[threading.Thread, queue.Queue[RunProgress]]":
    """Starts the live-run sequence in a background thread and returns the
    ``(thread, progress_queue)`` handle. The thread is started before this
    function returns; the caller is responsible for draining the queue."""
    progress_queue: "queue.Queue[RunProgress]" = queue.Queue()

    def _run() -> None:
        try:
            progress_queue.put(RunProgress(stage="starting"))

            import agent_eval.evaluators  # noqa: F401  (registers built-in evaluators)
            from inspect_ai import eval as inspect_eval

            from agent_eval.trace.inspect_adapter import eval_log_to_trajectories

            scenario = load_scenario(scenario_path)
            task_factory = resolve_task_factory(task_factory_dotted)
            task = task_factory(candidate_path=candidate_path)

            progress_queue.put(RunProgress(stage="running"))
            logs = inspect_eval(task, model=model, log_dir=str(log_dir), display="none")
            log = logs[0]
            if log.status != "success":
                progress_queue.put(
                    RunProgress(stage="error", error=f"inspect eval failed: {log.error}")
                )
                return

            trajectories = eval_log_to_trajectories(log, scenario_id=scenario.id)
            trajectory = trajectories[0]

            progress_queue.put(RunProgress(stage="evaluating", trajectory=trajectory))
            report = run_engine(scenario, trajectory)
            progress_queue.put(RunProgress(stage="done", report=report, trajectory=trajectory))
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI, never crash silently
            progress_queue.put(
                RunProgress(stage="error", error=str(exc), detail=traceback.format_exc())
            )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread, progress_queue
