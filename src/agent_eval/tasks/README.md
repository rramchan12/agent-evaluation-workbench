# tasks/

The only part of this package that talks directly to Inspect AI's execution
model. Each file here is an Inspect `@task` definition — what `inspect eval`
actually runs.

This is where the choice between two integration paths is made, per
scenario:

- **Native tool loop** (implemented, `decision_brief.py`) — Inspect `@tool`
  functions plus a `use_tools(...)` + `generate(tool_calls="loop")` solver.
  Inspect drives the loop itself and captures full, structured tool-call
  evidence automatically; `trace/inspect_adapter.py` normalizes the
  resulting eval log into a `Trajectory`.
- **Bridged external agent** (not yet implemented) — a real Cowork/Copilot-
  style product run via `agent_bridge()` (in-process) or
  `sandbox_agent_bridge()` (CLI agents in a sandbox, e.g. Claude Code, Codex
  CLI). Inspect only intercepts model traffic; tool-level evidence
  completeness depends on what the bridged agent's own protocol exposes.

The model the agent uses (`--model ...`) is always a runtime parameter, never
hardcoded here — this keeps a scenario runnable against different candidate
agents without touching this code.

`agent-eval run` (in `cli.py`) invokes Inspect's `eval()` API directly
against the task factory named on the command line
(`--task module.path:function_name`), so no separate `runner.py` wrapper is
needed.
