# expected/

Ground-truth verdicts for each trace in `traces/` — what every requirement
should evaluate to, and what the final release decision should be. This
turns the flagship demonstration into a regression test: `tests/integration/`
replays a trace and asserts its result matches the corresponding file here.
