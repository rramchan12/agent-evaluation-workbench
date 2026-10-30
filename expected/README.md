# expected/

Ground-truth verdicts for each recorded trace in `traces/` — what every
requirement should evaluate to, and what the final release decision should
be. This turns the `coding-agent-bugfix` scenario into a regression test:
`tests/integration/test_coding_bugfix_scenario.py` replays a trace and
asserts its result matches the corresponding file here
(`coding-bugfix-good.json`, `coding-bugfix-bad.json`).

The `controlled-workspace-decision-brief` scenario does not use this
directory: it is run live via Inspect + a scripted mockllm, so its expected
verdicts live scenario-locally instead, under
`scenarios/controlled-workspace-decision-brief/expected/`.
