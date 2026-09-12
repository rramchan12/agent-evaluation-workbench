# tests/unit/

Tests for individual pieces of `src/agent_eval/core/` and
`src/agent_eval/evaluators/` in isolation — e.g. that `allow_list_policy`
correctly fails when a configured field's value is outside the allow list,
or that `reconciliation.py` gives a deterministic result precedence over a
conflicting semantic judgment.

These tests should not require Inspect AI, a scenario, or any recorded trace
file — only the specific module under test and small, inline fixtures.
