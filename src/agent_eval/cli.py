"""Command-line entry point: ``agent-eval run`` and ``agent-eval evaluate``.

``run`` drives a live Inspect AI task and evaluates the resulting trajectory.
``evaluate`` replays a previously recorded trajectory against a scenario with
zero model/Inspect involvement -- this is what proves evaluators are
reproducible independently of the agent that produced the trace
(Definition-of-Done item 5). It accepts either a saved ``Trajectory`` JSON
(from ``--save-trajectory``) or a hand-authored recorded-trace JSON (the
``traces/`` fixture shape consumed by ``import_recorded_trace``).
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

# Importing this registers every built-in deterministic/semantic evaluator.
import agent_eval.evaluators  # noqa: F401
from agent_eval.core.engine import evaluate as run_engine
from agent_eval.core.requirements import load_scenario
from agent_eval.reporting.render import write_html_report, write_json_report
from agent_eval.trace.model import Trajectory


def _write_reports(report, out_dir: Path, formats: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if "json" in formats:
        write_json_report(report, out_dir / "report.json")
    if "html" in formats:
        write_html_report(report, out_dir / "report.html")


def _print_summary(report) -> None:
    print(f"scenario: {report.scenario_id}  trajectory: {report.trajectory_id}")
    print(f"release decision: {report.release_decision.decision}")
    for r in report.requirement_results:
        print(f"  [{r.verdict:>22}] {r.requirement.id} ({r.requirement.kind}, {r.requirement.importance})")


def _resolve_task_factory(dotted: str):
    """Resolve ``module.path:function_name`` into a callable Inspect task factory."""
    module_name, _, func_name = dotted.partition(":")
    if not func_name:
        raise ValueError(f"--task must be 'module.path:function_name', got {dotted!r}")
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def cmd_run(args: argparse.Namespace) -> int:
    from inspect_ai import eval as inspect_eval

    from agent_eval.trace.inspect_adapter import eval_log_to_trajectories

    scenario = load_scenario(args.scenario)
    task_factory = _resolve_task_factory(args.task)
    task = task_factory(candidate_path=args.candidate)

    logs = inspect_eval(
        task,
        model=args.model,
        log_dir=args.log_dir,
        display="none",
    )
    log = logs[0]
    if log.status != "success":
        print(f"inspect eval failed: {log.error}", file=sys.stderr)
        return 1

    trajectories = eval_log_to_trajectories(log, scenario_id=scenario.id)
    exit_code = 0
    for trajectory in trajectories:
        if args.save_trajectory:
            trajectory.save(args.save_trajectory)
        report = run_engine(scenario, trajectory)
        _print_summary(report)
        if args.out_dir:
            _write_reports(report, Path(args.out_dir), args.format)
        if report.release_decision.decision in ("FAIL",):
            exit_code = 1
    return exit_code


def _load_trajectory(path: str | Path):
    """Loads a trajectory file, accepting either a saved ``Trajectory`` JSON
    (produced by ``Trajectory.save`` / ``--save-trajectory``) or a recorded
    step-list JSON (the ``traces/`` fixture shape consumed by
    ``import_recorded_trace``). Distinguished by the presence of a
    top-level ``"steps"`` key, which only the recorded-trace shape has.
    """
    from agent_eval.trace.import_recorded import import_recorded_trace

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "steps" in data:
        return import_recorded_trace(path)
    return Trajectory.from_dict(data)


def cmd_evaluate(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario)
    trajectory = _load_trajectory(args.trajectory)
    report = run_engine(scenario, trajectory)
    _print_summary(report)
    if args.out_dir:
        _write_reports(report, Path(args.out_dir), args.format)
    return 1 if report.release_decision.decision == "FAIL" else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="Run an Inspect AI task and evaluate the resulting trajectory."
    )
    run_parser.add_argument("--scenario", required=True, help="Path to scenario.json")
    run_parser.add_argument(
        "--task", required=True, help="Inspect task factory as 'module.path:function_name'"
    )
    run_parser.add_argument(
        "--candidate", required=True, help="Path to a candidate step-list JSON file"
    )
    run_parser.add_argument("--model", default="mockllm/model", help="Inspect model name")
    run_parser.add_argument("--log-dir", default="inspect-logs", help="Inspect eval log directory")
    run_parser.add_argument("--save-trajectory", help="Path to save the normalized Trajectory JSON")
    run_parser.add_argument("--out-dir", help="Directory to write report.json/report.html into")
    run_parser.add_argument(
        "--format", nargs="+", choices=["json", "html"], default=["json", "html"]
    )
    run_parser.set_defaults(func=cmd_run)

    eval_parser = subparsers.add_parser(
        "evaluate", help="Evaluate a saved Trajectory JSON against a scenario (no Inspect/model calls)."
    )
    eval_parser.add_argument("--scenario", required=True, help="Path to scenario.json")
    eval_parser.add_argument(
        "--trajectory",
        required=True,
        help="Path to a saved Trajectory JSON or a recorded step-list trace JSON",
    )
    eval_parser.add_argument("--out-dir", help="Directory to write report.json/report.html into")
    eval_parser.add_argument(
        "--format", nargs="+", choices=["json", "html"], default=["json", "html"]
    )
    eval_parser.set_defaults(func=cmd_evaluate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
