# traces/

Recorded trajectories, used for evaluator-only replay — running the
evaluation pipeline with zero agent execution. A trace here can come from
any source: a live Inspect run's eval log (normalized via
`src/agent_eval/trace/inspect_adapter.py`), a hand-authored fixture, or a
future adapter's export.

This is where the paired flagship trajectories for
`scenarios/controlled-workspace-decision-brief/` live once recorded:
one valid trajectory, and one correct-output/invalid-process trajectory.

See `expected/` for the verdicts each trace is expected to produce.
