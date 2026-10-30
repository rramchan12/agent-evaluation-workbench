# traces/

Recorded trajectories, used for evaluator-only replay — running the
evaluation pipeline with zero agent execution. A trace here can come from
any source: a live run's eval log, a hand-authored fixture, or a future
adapter's export. Loaded via
`src/agent_eval/trace/import_recorded.py:import_recorded_trace`.

This is where the paired `coding-agent-bugfix` trajectories live:
`coding-bugfix-good.json` (reads the failing test, fixes the bug, reruns
tests, which pass after the last edit) and `coding-bugfix-bad.json` (never
reads the failing test, edits the protected test file to fake a pass, then
makes an unverified final edit).

The `controlled-workspace-decision-brief` scenario does not use this
directory — it runs live via Inspect + a scripted mockllm instead
(`src/agent_eval/tasks/decision_brief.py`), with its trajectories normalized
by `src/agent_eval/trace/inspect_adapter.py` rather than recorded here.

See `expected/` for the verdicts each trace is expected to produce.
