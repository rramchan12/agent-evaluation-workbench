# Test Report

**Date:** 2026-10-30
**Branch:** `implement-test-the-changes-create-a-test-report-an`
**Command:** `python -m pytest -q` / `python -m pytest -v`
**Result:** 35 passed, 0 failed, 34 warnings (deprecation warning from
`inspect_ai`'s retry backoff, unrelated to this repo's code)

## Scope

This report covers the full test suite as it exists on this branch: the
pre-existing Stage 1 harness tests (unit + integration, committed on this
branch ahead of `main`) plus four new repository-structure tests added as
part of this change (`tests/unit/test_repo_structure.py`).

## Summary by file

| File | Tests | Outcome |
|---|---|---|
| `tests/integration/test_coding_bugfix_scenario.py` | 4 | all passed |
| `tests/integration/test_decision_brief_scenario.py` | 4 | all passed |
| `tests/unit/test_evaluators.py` | 12 | all passed |
| `tests/unit/test_reconciliation_release.py` | 10 | all passed |
| `tests/unit/test_repo_structure.py` (new) | 4 | all passed |
| **Total** | **35** | **35 passed** |

## New repository-structure tests

Added in this change, per the implementation plan, to guard the
repository's documentation/layout conventions:

1. `test_top_level_docs_exist` — `README.md`, `ARCHITECTURE.md`, and
   `IDEATION.md` exist at the repo root. **PASS**
2. `test_every_layout_dir_has_a_readme` — every directory that owns at
   least one git-tracked file has its own `README.md`. **PASS** (after
   fix — see below)
3. `test_no_markdown_file_is_empty` — no tracked `.md` file is blank.
   **PASS**
4. `test_relative_markdown_links_resolve` — every relative (non-http,
   non-anchor) markdown link target resolves to an existing path.
   **PASS**

### Gap found and fixed

The first run of `test_every_layout_dir_has_a_readme` failed: three
directories held tracked files but no `README.md`:

- `scenarios/coding-agent-bugfix/`
- `scenarios/controlled-workspace-decision-brief/candidates/`
- `scenarios/controlled-workspace-decision-brief/expected/`

Added a `README.md` to each, matching the style and level of detail of
sibling directories (`scenarios/controlled-workspace-decision-brief/workspace/README.md`,
`.../template/README.md`). All four structure tests pass after the fix.

## Full test list

```
tests/integration/test_coding_bugfix_scenario.py::test_recorded_coding_trace_matches_expected_verdicts[coding-bugfix-good] PASSED
tests/integration/test_coding_bugfix_scenario.py::test_recorded_coding_trace_matches_expected_verdicts[coding-bugfix-bad] PASSED
tests/integration/test_coding_bugfix_scenario.py::test_cli_evaluate_auto_detects_recorded_trace_format[coding-bugfix-good-0] PASSED
tests/integration/test_coding_bugfix_scenario.py::test_cli_evaluate_auto_detects_recorded_trace_format[coding-bugfix-bad-1] PASSED
tests/integration/test_decision_brief_scenario.py::test_candidate_matches_expected_verdicts[candidate-1] PASSED
tests/integration/test_decision_brief_scenario.py::test_candidate_matches_expected_verdicts[candidate-2] PASSED
tests/integration/test_decision_brief_scenario.py::test_replay_from_saved_trajectory_matches_live_run[candidate-1] PASSED
tests/integration/test_decision_brief_scenario.py::test_replay_from_saved_trajectory_matches_live_run[candidate-2] PASSED
tests/unit/test_evaluators.py::test_select_evidence_filters_by_tool_name PASSED
tests/unit/test_evaluators.py::test_select_evidence_filters_by_argument_glob PASSED
tests/unit/test_evaluators.py::test_required_inspection_fails_when_missing_value PASSED
tests/unit/test_evaluators.py::test_required_inspection_passes_when_all_values_present PASSED
tests/unit/test_evaluators.py::test_forbidden_access_fails_on_forbidden_value PASSED
tests/unit/test_evaluators.py::test_forbidden_access_passes_when_clean PASSED
tests/unit/test_evaluators.py::test_verify_after_last_write_fails_when_validate_before_write PASSED
tests/unit/test_evaluators.py::test_verify_after_last_write_passes_when_validate_after_write PASSED
tests/unit/test_evaluators.py::test_artifact_sections_detects_missing_section PASSED
tests/unit/test_evaluators.py::test_citations_observed_fails_on_unobserved_citation PASSED
tests/unit/test_evaluators.py::test_last_result_matches_checks_last_event_only PASSED
tests/unit/test_evaluators.py::test_fake_judge_fails_when_keyword_missing PASSED
tests/unit/test_evaluators.py::test_evaluators_abstain_on_incomplete_trajectory PASSED
tests/unit/test_reconciliation_release.py::test_deterministic_fail_overrides_passing_semantic_judge PASSED
tests/unit/test_reconciliation_release.py::test_semantic_disagreement_gives_review_required PASSED
tests/unit/test_reconciliation_release.py::test_incomplete_trajectory_gives_insufficient_evidence PASSED
tests/unit/test_reconciliation_release.py::test_abstaining_evaluator_gives_insufficient_evidence_even_if_complete PASSED
tests/unit/test_reconciliation_release.py::test_all_pass_gives_pass PASSED
tests/unit/test_reconciliation_release.py::test_release_fails_on_blocker_fail PASSED
tests/unit/test_reconciliation_release.py::test_release_fail_cannot_be_offset_by_other_passes PASSED
tests/unit/test_reconciliation_release.py::test_release_review_required_when_no_blocking_fail PASSED
tests/unit/test_reconciliation_release.py::test_release_insufficient_evidence_when_no_fail_or_review PASSED
tests/unit/test_reconciliation_release.py::test_release_pass_when_everything_passes PASSED
tests/unit/test_repo_structure.py::test_top_level_docs_exist PASSED
tests/unit/test_repo_structure.py::test_every_layout_dir_has_a_readme PASSED
tests/unit/test_repo_structure.py::test_no_markdown_file_is_empty PASSED
tests/unit/test_repo_structure.py::test_relative_markdown_links_resolve PASSED
```

## Notes

- This change was produced from an implementation plan with
  `implementationReviewStatus: unreviewed` — it has not gone through the
  human plan-review workflow. Normal PR review, CI, and branch-protection
  rules still apply.
- The plan's second task (apply `ARCHITECTURE.md` §6.1 "Repository
  layout" per `planner/architecture-update.md`) was **not done**: no
  `planner/architecture-update.md` file exists anywhere in this repository
  or in the plan's source directory, so there is no content to apply.
