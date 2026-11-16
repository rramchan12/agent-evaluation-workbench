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
- the recorded trace of the agent's run lives under the top-level `traces/`
  directory, with its expected verdicts in `expected/` (or scenario-locally, as for
  `controlled-workspace-decision-brief`)

The agent being evaluated runs outside this harness; only its recorded trace is supplied — it is never
part of a scenario definition.

## judge-calibration/

Not a scenario (there is no agent, no requirement hierarchy, no release
policy) — it is a calibration fixture for `agent-eval calibrate`
(`core/calibration.py`): a hand-labeled set of evidence bundles and their
known-correct verdicts, used to measure a judge's accuracy before trusting
it in a real scenario. See `evaluators/semantic/README.md` for the cases
file format.

