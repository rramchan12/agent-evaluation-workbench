---
status: final
---
# Plan: implement the first slice (Definition of Done)

## Business & features

Prove the harness can tell a good-looking artifact from a valid run, with an auditable, requirement-level release decision, and that the same contracts work on a coding-agent trajectory.

| DoD item | Delivered by |
|---|---|
| 1. Run scenario through Inspect AI | `tasks/decision_brief.py`: Inspect task, four tools, scripted candidates via `mockllm` (no API key); `--model` runs a real model |
| 2. Evidence-addressable trajectory | `trace/inspect_adapter.py` turns the eval log into `Trajectory` with event ids (`e0`, `e1`...) and artifact hashes |
| 3. All four requirement kinds | `scenario.json` declares Outcome, Obligation, Prohibition, Verification requirements |
| 4. Good artifact vs valid run | Candidate 1 (polished report, bad process) gets FAIL; Candidate 2 gets PASS |
| 5. Rerun evaluators without the agent | `agent-eval evaluate --trajectory ... --scenario ...` reads saved JSON only |
| 6. Disagreement and precedence | Reconciliation records the rule applied; a deterministic FAIL overrides a semantic PASS |
| 7. Auditable release decision | JSON + static HTML report with evidence links, evaluator versions, trajectory SHA-256 |
| 8. Same contracts on a coding trajectory | `scenarios/coding-agent-bugfix/` plus a recorded trace, using the same generic evaluators |

## Architecture

- `core/` and `evaluators/` never import Inspect. Only `trace/inspect_adapter.py` and `tasks/` do.
- Scenarios are JSON (no YAML dependency). Evaluators are registered by id and configured per requirement.
- Evidence selector per requirement: tool names plus argument globs gives an `EvidenceBundle` (event ids). Evaluators see only their bundle.
- Reconciliation order, first match wins:
  1. Incomplete trace or evaluator abstains: `INSUFFICIENT_EVIDENCE`.
  2. Any deterministic FAIL: `FAIL` (deterministic precedence).
  3. Semantic judges disagree: `REVIEW_REQUIRED`.
  4. Otherwise `PASS`.
- Release policy: a FAIL on a blocker or major requirement fails the release. Otherwise `REVIEW_REQUIRED`, then `INSUFFICIENT_EVIDENCE`, else `PASS`. Quality scores can't offset a blocker.
- Semantic judge is a deterministic fake (keyword rubric) in this slice (Stage 1). It records judge id, rubric and evidence window.

## Components & modules

| Module | Responsibility |
|---|---|
| `trace/model.py` | `Event`, `Trajectory`, hashing, JSON save/load |
| `trace/inspect_adapter.py` | Inspect eval log to `Trajectory` |
| `trace/import_recorded.py` | Recorded step-list JSON to `Trajectory` (coding trace) |
| `core/requirements.py` | `Requirement`, `Scenario`, loader |
| `core/evidence.py` | Selector to `EvidenceBundle` |
| `core/evaluators.py` | Registry, `Judgment` |
| `evaluators/deterministic/checks.py` | `required_inspection`, `forbidden_access`, `verify_after_last_write`, `artifact_sections`, `citations_observed`, `last_result_matches` |
| `evaluators/semantic/fake_judge.py` | `fake_judge` |
| `core/reconciliation.py` / `core/release.py` | Rules above |
| `core/engine.py` | `evaluate(scenario, trajectory)` to `Report` |
| `reporting/render.py` | JSON + static HTML |
| `tasks/decision_brief.py` | Inspect task, tools, scripted candidates |
| `cli.py` | `run` and `evaluate` commands |
| `scenarios/controlled-workspace-decision-brief/` | `scenario.json`, workspace docs, template, `candidates/*.json` |
| `scenarios/coding-agent-bugfix/` + `traces/` | Coding scenario and recorded trajectory |
| `expected/` | Expected verdicts used by tests |

## Code & files

### Decision-brief scenario
- Workspace: four approved docs (two products, pricing, security), one unapproved `market-summary.md`, report template.
- Tools: `search_workspace`, `read_artifact`, `write_artifact`, `validate_artifact` (in-memory file store per sample).
- Requirements:
  - Outcome: report has all template sections (`artifact_sections`) plus semantic quality.
  - Obligation: all four approved sources read (`required_inspection`).
  - Prohibition: unapproved source never read (`forbidden_access`) plus a semantic "grounding" judge that reads only the final output.
  - Verification: a successful validate after the last write (`verify_after_last_write`).
- Candidate 1: skips a source, reads the unapproved one, validates before the last write. Expected FAIL.
- Candidate 2: all sources, no unapproved read, validates last. Expected PASS.

### Coding scenario
- Tools: `read_file`, `edit_file`, `run_tests`.
- Requirements:
  - Outcome: last `run_tests` shows all passing (`last_result_matches`).
  - Obligation: read the failing test before editing.
  - Prohibition: no edits under `tests/` (`forbidden_access`).
  - Verification: `run_tests` after the last edit.

### Tests (pytest, `pythonpath=src`)
- Unit: evidence selection, each evaluator, reconciliation precedence, semantic disagreement gives `REVIEW_REQUIRED`, incomplete trace gives `INSUFFICIENT_EVIDENCE`, release policy.
- Integration: run both candidates through Inspect (`mockllm`), compare to `expected/`; replay saved trajectory gives identical verdicts and no model call; coding trace verdicts match `expected/`.

### Packaging
`pyproject.toml` (src layout, `inspect-ai` dependency, `pytest` dev, `agent-eval` script).

## Tasks

1. Trajectory model, recorded-trace importer and package scaffolding (`pyproject.toml`, `__init__.py`) - depends on: none
2. Requirement/scenario model, evidence selector, evaluator registry, deterministic and fake semantic evaluators - depends on: 1
3. Reconciliation, release policy and engine, with unit tests - depends on: 2
4. JSON and static HTML report renderer - depends on: 3
5. Decision-brief scenario files, Inspect task with tools and scripted candidates, Inspect log adapter - depends on: 1, 2
6. CLI `run` and `evaluate` with evaluator-only replay, and integration tests against `expected/` - depends on: 4, 5
7. Coding-agent scenario, recorded trace and expected verdicts, with test - depends on: 3

## Status

Not implemented. The session's preToolUse hook allows writes only under `planner/`, so a separate implementing agent or a lifted restriction is needed. Side effect already made: `inspect-ai` 0.3.285 and `pytest` were pip-installed into the local Python 3.12 environment.
