# scenarios/

The "test rack": declarative task definitions with no code and no agent
inside them. Each subfolder is one scenario — the task, the fixture content
the agent acts against, the requirement hierarchy, and the release policy.

A scenario contains:

- `scenario.json` — the task/requirement hierarchy and release policy in one
  document: `id`, `metadata` (task-specific config such as doc allow-lists),
  and `requirements[]`, where each requirement declares its `kind`
  (outcome/obligation/prohibition/verification), its `evidence` selector,
  and the evaluators that judge it. Each evaluator entry references an
  evaluator **by ID and config only** (see
  `src/agent_eval/evaluators/README.md`) — never new evaluator code
- fixture content (a `template/`, a `workspace/`, or similar) — whatever the
  agent needs to act against
- for scenarios evaluated from a recorded trace rather than a live Inspect
  run (e.g. `coding-agent-bugfix`), the corresponding trace lives under the
  top-level `traces/` directory, with its expected verdicts in `expected/`

The agent being evaluated is supplied externally, at run time — it is never
part of a scenario definition.
