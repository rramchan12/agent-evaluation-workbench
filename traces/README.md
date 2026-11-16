# traces/

Recorded trajectories, used for evaluator-only replay — running the
evaluation pipeline with zero agent execution. A trace here can come from
any source: a hand-authored fixture, or an adapter's normalization of an
external runtime's log. The harness itself never produces a trace by running
an agent. Loaded via
`src/agent_eval/trace/import_recorded.py:import_recorded_trace`.

This is where the paired `coding-agent-bugfix` trajectories live:
`coding-bugfix-good.json` (reads the failing test, fixes the bug, reruns
tests, which pass after the last edit) and `coding-bugfix-bad.json` (never
reads the failing test, edits the protected test file to fake a pass, then
makes an unverified final edit). `coding-bugfix-insufficient.json` is a
trimmed copy of the good trace with `"complete": false` and an
`"incompleteness_reason"`, used to exercise the GUI's and reconciliation's
`INSUFFICIENT_EVIDENCE` path for a truncated trace.

`decision-brief-candidate-1.json` and `decision-brief-candidate-2.json` are the
paired traces for `controlled-workspace-decision-brief`: candidate 1 skips a
required source, reads an unapproved one, and validates before its last write
(expected `FAIL`); candidate 2 is a valid process (expected `PASS`). Their
expected verdicts live under
`scenarios/controlled-workspace-decision-brief/expected/`.

See `expected/` for the verdicts each coding-bugfix trace is expected to produce.
