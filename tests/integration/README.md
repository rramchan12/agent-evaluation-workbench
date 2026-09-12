# tests/integration/

Full-pipeline tests: load a scenario from `scenarios/`, replay a recorded
trajectory from `traces/`, run the evaluation pipeline end to end, and assert
the result matches the corresponding file in `expected/`.

No agent is executed here — this exercises the same evaluator-only replay
path as `agent-eval evaluate`, which is the property ARCHITECTURE.md requires
before any live Inspect execution is added.
