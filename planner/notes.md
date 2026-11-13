# Notes: Open Agent Evaluation Harness

## 1. What this is

A replay-capable harness that checks whether Cowork- and Copilot-style agents
meet declared requirements through an acceptable, evidenced trajectory, not
just whether the final output looks correct.

**Status:** planning and scaffolding only. The repo has design docs
(`IDEATION.md`, `ARCHITECTURE.md`) and a folder skeleton, with no implementation.

```text
src/agent_eval/   harness package (core, trace, tasks, evaluators, reporting)
scenarios/        declarative task definitions
traces/           recorded trajectories for evaluator-only replay
expected/         ground-truth verdicts for tests
tests/            unit and integration tests
```

## 2. Architecture in brief

**Core question:** did the agent satisfy the declared requirements through an
acceptable and evidenced trajectory? The unit of evaluation is the
*requirement*, not an aggregate score.

**Pipeline:**

1. Scenario declares the task, requirements and fixtures.
2. Inspect AI runs the agent against a controlled environment.
3. Execution yields a trace, artifacts and native scorer results.
4. The evaluation extension selects an evidence bundle per requirement.
5. Evaluators (deterministic, semantic, later human) judge independently.
6. Reconciliation plus release policy produce an evidence-backed result.

**Boundaries**

| Area | Contains |
|---|---|
| System under test | Agent runtime, model, prompts, config, memory, tool-selection, MCP client |
| Controlled environment | Tools, workspace, fixtures, sandbox, injected failures (versioned, reset) |
| Evaluation system | Scenarios, evidence selection, evaluators, reconciliation, release policy, reports |

A judge model is a measuring instrument, not part of the system under test.

**Requirement kinds:** Outcome, Obligation, Prohibition, Verification.

**Reconciliation rules**

- A deterministic violation beats a positive semantic score.
- Semantic disagreement gives `REVIEW_REQUIRED`.
- Missing mandatory trace data gives `INSUFFICIENT_EVIDENCE`.
- A verified blocker failure fails the release; quality scores can't offset it.

**Responsibility split**

- Inspect AI owns execution, tools, sandbox, limits, scorers and logs.
- The extension owns requirements, evidence selection, temporal/policy
  evaluation, judge integration, reconciliation, release decision and report
  (JSON plus static HTML).

**Reference scenario:** a controlled-workspace decision brief. Candidate 1 has a
polished report but skips a required source, opens the unapproved summary and
skips final validation, so it fails release. Candidate 2 passes.

## 3. Build stages

| Stage | Outcome |
|---|---|
| 0 | Probe Inspect extension points (trace, scorers, replay, artifacts, report) |
| 1 | One complete artifact scenario: deterministic evaluators, fake judge, reconciliation, replay, report |
| 2 | Apply the same contracts to a recorded coding-agent trajectory |
| 3 | Real judge, calibration, abstention, human review |
| 4 | Adapters, repeated-run analysis, baselines, CI release gates |
| 5 | Decide what to extract (stay extension, upstream, fork, or small kernel) |

## 4. Inspect AI vs Azure AI Foundry

*Source: what-is, from general knowledge, not web-verified.*

- **Inspect AI:** open, vendor-neutral runner with sandboxes, agent bridges,
  scorers, logs/viewer and resume.
- **Foundry:** managed safety/quality evaluators, dashboards and governance,
  but coupled to Azure.
- **Recommendation:** use Inspect as the runner. Treat Foundry evaluators as
  optional scorers or an export target. This matches the decision in
  `ARCHITECTURE.md`.

## 5. Open decisions

- Inspect version and supported extension points
- Persisted requirement and evidence contracts
- Minimum normalized trace representation
- How artifacts and state changes are referenced
- Evaluator interface and isolation
- Temporal rule representation
- Reconciliation and release-policy configuration
- Trace completeness and redaction rules
- Evaluator-only replay design
- Report format and evidence navigation
- Test strategy (valid, invalid, insufficient-evidence trajectories)
- Confidence semantics across evaluator types
- Granularity of a new system-under-test version

## 6. Definition of done (first slice)

1. Run the scenario through Inspect AI.
2. Record an evidence-addressable trajectory.
3. Evaluate all four requirement kinds.
4. Tell a good artifact from a valid run.
5. Rerun evaluators without rerunning the agent.
6. Explain disagreement and deterministic precedence.
7. Produce an auditable requirement-level release decision.
8. Apply the same contracts to one recorded coding-agent trajectory.
