# scenarios/

The "test rack": declarative task definitions with no code and no agent
inside them. Each subfolder is one scenario — the task, the fixture content
the agent acts against, the requirement hierarchy, and the release policy.

A scenario contains:

- `scenario.yaml` — the task and what tools/fixture apply
- `requirements.yaml` — the requirement hierarchy; each requirement
  references an evaluator **by ID and config only** (see
  `src/agent_eval/evaluators/README.md`) — never new evaluator code
- `release-policy.yaml` — the acceptance criteria that turn requirement
  verdicts into a release decision
- fixture content (a `template/`, a `workspace/`, or similar) — whatever the
  agent needs to act against

The agent being evaluated is supplied externally, at run time — it is never
part of a scenario definition.
