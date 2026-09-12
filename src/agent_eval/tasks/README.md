# tasks/

The only part of this package that talks directly to Inspect AI's execution
model. Each file here is an Inspect `@task` definition — what `inspect eval`
actually runs.

This is where the choice between two integration paths is made, per
scenario:

- **Native tool loop** — an Inspect `react()` (or custom) agent using
  Inspect-registered tools. Inspect drives the loop itself and captures full,
  structured tool-call evidence automatically.
- **Bridged external agent** — a real Cowork/Copilot-style product run via
  `agent_bridge()` (in-process) or `sandbox_agent_bridge()` (CLI agents in a
  sandbox, e.g. Claude Code, Codex CLI). Inspect only intercepts model
  traffic; tool-level evidence completeness depends on what the bridged
  agent's own protocol exposes.

The model the agent uses (`--model ...`) is always a runtime parameter, never
hardcoded here — this keeps a scenario runnable against different candidate
agents without touching this code.

A `runner.py` (not yet created) will wrap Inspect's Python `eval()` API so
`agent-eval run` can invoke a task programmatically rather than shelling out
to the `inspect` CLI.
