# Test Report

**Date:** 2026-11-12
**Baseline:** `main` at `29553b4`/`3b48c21` (Stages 1-3, PRs #6 and #7) plus the
`scenarios/judge-calibration/README.md` fix from PR #8
**Command:** `python -m pytest -v`
**Result:** 85 passed, 0 failed (previous report, 2026-10-30: 35 passed)

## Scope

The full suite: Stage 1 harness, Stage 2 recorded-trace scenario, the
repository-structure guards, the Stage 3 real judge / calibration / human
review additions, and the Streamlit GUI helpers and flows.

## Summary by file

| File | Tests | Outcome |
|---|---|---|
| `tests/integration/test_cli_review_calibrate.py` | 4 | all passed |
| `tests/integration/test_coding_bugfix_scenario.py` | 4 | all passed |
| `tests/integration/test_decision_brief_scenario.py` | 4 | all passed |
| `tests/integration/test_gui_flows.py` | 9 | all passed |
| `tests/unit/test_calibration.py` | 3 | all passed |
| `tests/unit/test_evaluators.py` | 13 | all passed |
| `tests/unit/test_gui_formatting.py` | 10 | all passed |
| `tests/unit/test_gui_scenario_catalog.py` | 6 | all passed |
| `tests/unit/test_gui_trajectory_loader.py` | 3 | all passed |
| `tests/unit/test_human_review.py` | 4 | all passed |
| `tests/unit/test_judges.py` | 11 | all passed |
| `tests/unit/test_reconciliation_release.py` | 10 | all passed |
| `tests/unit/test_repo_structure.py` | 4 | all passed |
| **Total** | **85** | **85 passed** |

## Changes since the previous report

- **+50 tests** from Stage 3 (judges, calibration, human review, review/
  calibrate CLI) and the GUI (formatting, catalog, loader, flows).
- `test_every_layout_dir_has_a_readme` failed on `main` after Stage 3
  because `scenarios/judge-calibration/` had no `README.md`; fixed by
  adding one (PR #8). The test enforces that every directory owning a
  tracked file has its own README.

## Known gaps

- Judge calibration runs against scripted (`mockllm`) responses only; no
  test exercises a live model judge, so real-judge accuracy is unmeasured.
- `required_inspection` is presence-only; there is no ordering test
  because there is no ordering evaluator yet (see `ARCHITECTURE.md` §0).
- No tests exist for Stage 4 (OTel / trace-store import, CI gate).

Run `python -m pytest -v` for the per-test listing.
