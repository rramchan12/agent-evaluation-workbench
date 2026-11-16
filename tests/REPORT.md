# Test Report

**Date:** 2026-11-16
**Branch:** `remove_inspect_ai_coupling`
**Command:** `python -m pytest -q` / `python -m pytest -v`
**Result:** 86 passed, 0 failed

## Scope

The full unit and integration suite. The harness never runs an agent, so every
test evaluates a recorded trace (`traces/`), a scenario fixture, or an
in-memory object. The judge tests use scripted `mock/...` model responses (no
network, no API key). This revision removes the Inspect AI coupling and the
native runner, so there are no `inspect_ai` warnings and no live-run tests;
the decision-brief integration tests now replay
`traces/decision-brief-candidate-N.json` and compare to
`scenarios/controlled-workspace-decision-brief/expected/`.

Not covered: the `openai/...` HTTP path of `OpenAICompatibleClient` against
a real endpoint.

## Summary by file

| File | Tests | Outcome |
|---|---|---|
| `tests/integration/test_cli_review_calibrate.py` | 4 | all passed |
| `tests/integration/test_coding_bugfix_scenario.py` | 4 | all passed |
| `tests/integration/test_decision_brief_scenario.py` | 4 | all passed |
| `tests/integration/test_gui_flows.py` | 8 | all passed |
| `tests/unit/test_calibration.py` | 3 | all passed |
| `tests/unit/test_evaluators.py` | 13 | all passed |
| `tests/unit/test_gui_formatting.py` | 10 | all passed |
| `tests/unit/test_gui_scenario_catalog.py` | 5 | all passed |
| `tests/unit/test_gui_trajectory_loader.py` | 3 | all passed |
| `tests/unit/test_human_review.py` | 4 | all passed |
| `tests/unit/test_judges.py` | 11 | all passed |
| `tests/unit/test_model_client.py` | 3 | all passed |
| `tests/unit/test_reconciliation_release.py` | 10 | all passed |
| `tests/unit/test_repo_structure.py` | 4 | all passed |
| **Total** | **86** | **86 passed** |

## Full test list

```
tests/integration/test_cli_review_calibrate.py::test_cli_review_lists_items_needing_review PASSED
tests/integration/test_cli_review_calibrate.py::test_cli_review_applies_decisions_and_recomputes_release PASSED
tests/integration/test_cli_review_calibrate.py::test_cli_calibrate_scores_fixture_cases PASSED
tests/integration/test_cli_review_calibrate.py::test_cli_calibrate_nonzero_exit_below_min_accuracy PASSED
tests/integration/test_coding_bugfix_scenario.py::test_recorded_coding_trace_matches_expected_verdicts[coding-bugfix-good] PASSED
tests/integration/test_coding_bugfix_scenario.py::test_recorded_coding_trace_matches_expected_verdicts[coding-bugfix-bad] PASSED
tests/integration/test_coding_bugfix_scenario.py::test_cli_evaluate_auto_detects_recorded_trace_format[coding-bugfix-good-0] PASSED
tests/integration/test_coding_bugfix_scenario.py::test_cli_evaluate_auto_detects_recorded_trace_format[coding-bugfix-bad-1] PASSED
tests/integration/test_decision_brief_scenario.py::test_trace_matches_expected_verdicts[candidate-1] PASSED
tests/integration/test_decision_brief_scenario.py::test_trace_matches_expected_verdicts[candidate-2] PASSED
tests/integration/test_decision_brief_scenario.py::test_saved_trajectory_replay_matches_first_evaluation[candidate-1] PASSED
tests/integration/test_decision_brief_scenario.py::test_saved_trajectory_replay_matches_first_evaluation[candidate-2] PASSED
tests/integration/test_gui_flows.py::test_replay_pass_fixture_renders_pass_badge PASSED
tests/integration/test_gui_flows.py::test_replay_fail_fixture_renders_fail_badge_and_blocker_requirement PASSED
tests/integration/test_gui_flows.py::test_replay_insufficient_evidence_fixture_renders_that_verdict PASSED
tests/integration/test_gui_flows.py::test_replay_without_a_selected_trace_shows_readable_error PASSED
tests/integration/test_gui_flows.py::test_replay_decision_brief_valid_process_trace_passes PASSED
tests/integration/test_gui_flows.py::test_replay_decision_brief_invalid_process_trace_fails PASSED
tests/integration/test_gui_flows.py::test_review_page_applies_human_decision_and_recomputes_release PASSED
tests/integration/test_gui_flows.py::test_calibration_page_reports_accuracy PASSED
tests/unit/test_calibration.py::test_run_calibration_scores_correct_and_incorrect_cases PASSED
tests/unit/test_calibration.py::test_calibration_report_accuracy_is_zero_with_no_results PASSED
tests/unit/test_calibration.py::test_run_calibration_file_cases_fixture_scores_fully_accurate PASSED
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
tests/unit/test_gui_formatting.py::test_verdict_badge_matches_render_color_table PASSED
tests/unit/test_gui_formatting.py::test_verdict_badge_falls_back_for_unknown_verdict PASSED
tests/unit/test_gui_formatting.py::test_has_disagreement_true_when_multiple_verdicts PASSED
tests/unit/test_gui_formatting.py::test_has_disagreement_false_when_same_verdict PASSED
tests/unit/test_gui_formatting.py::test_has_disagreement_false_for_empty_or_single_judgment PASSED
tests/unit/test_gui_formatting.py::test_group_by_requirement_preserves_scenario_order PASSED
tests/unit/test_gui_formatting.py::test_group_by_requirement_insufficient_evidence_fixture PASSED
tests/unit/test_gui_formatting.py::test_group_by_requirement_fail_fixture PASSED
tests/unit/test_gui_formatting.py::test_resolve_evidence_resolves_known_ids_and_skips_unknown PASSED
tests/unit/test_gui_formatting.py::test_resolve_evidence_empty_for_no_ids PASSED
tests/unit/test_gui_scenario_catalog.py::test_discover_scenarios_finds_both_scenarios_alphabetically PASSED
tests/unit/test_gui_scenario_catalog.py::test_discover_traces_includes_decision_brief_recorded_traces PASSED
tests/unit/test_gui_scenario_catalog.py::test_discover_traces_finds_known_fixtures PASSED
tests/unit/test_gui_scenario_catalog.py::test_discover_traces_filters_by_scenario_id PASSED
tests/unit/test_gui_scenario_catalog.py::test_discover_traces_empty_for_unknown_scenario_id PASSED
tests/unit/test_gui_trajectory_loader.py::test_trajectory_from_path_loads_step_list_trace PASSED
tests/unit/test_gui_trajectory_loader.py::test_trajectory_from_path_loads_insufficient_evidence_trace PASSED
tests/unit/test_gui_trajectory_loader.py::test_trajectory_from_json_text_detects_saved_trajectory_shape PASSED
tests/unit/test_human_review.py::test_items_needing_review_includes_review_required_and_insufficient_evidence PASSED
tests/unit/test_human_review.py::test_apply_human_review_overrides_review_required_verdict PASSED
tests/unit/test_human_review.py::test_apply_human_review_leaves_undecided_requirements_unchanged PASSED
tests/unit/test_human_review.py::test_human_decision_from_dict PASSED
tests/unit/test_judges.py::test_parse_judge_response_valid_json PASSED
tests/unit/test_judges.py::test_parse_judge_response_invalid_json_is_insufficient_evidence PASSED
tests/unit/test_judges.py::test_parse_judge_response_non_object_json_is_insufficient_evidence PASSED
tests/unit/test_judges.py::test_parse_judge_response_unrecognized_verdict_is_insufficient_evidence PASSED
tests/unit/test_judges.py::test_parse_judge_response_non_numeric_confidence_is_dropped PASSED
tests/unit/test_judges.py::test_real_judge_pass_from_mock_response PASSED
tests/unit/test_judges.py::test_real_judge_fail_from_mock_response PASSED
tests/unit/test_judges.py::test_real_judge_abstains_on_incomplete_trajectory_without_calling_model PASSED
tests/unit/test_judges.py::test_real_judge_abstains_below_min_confidence PASSED
tests/unit/test_judges.py::test_real_judge_invalid_model_response_is_insufficient_evidence PASSED
tests/unit/test_judges.py::test_fake_and_real_judge_disagreement_gives_review_required PASSED
tests/unit/test_model_client.py::test_scripted_client_repeats_last_response PASSED
tests/unit/test_model_client.py::test_unknown_provider_is_rejected PASSED
tests/unit/test_model_client.py::test_openai_provider_requires_api_key PASSED
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
