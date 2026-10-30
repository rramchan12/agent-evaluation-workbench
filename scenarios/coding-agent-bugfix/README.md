# coding-agent-bugfix/

The Stage 2 recorded-trajectory scenario: a single `scenario.json` with no
fixture content of its own, proving the §6 core/evaluator contracts apply
unchanged to a non-Inspect trajectory.

The agent's task (described in `scenario.json`'s `description` and
`metadata`) is to fix a failing unit test in `src/calculator.py` by reading
the failing test, editing only production code, and re-running the test
suite after its final edit.

Unlike `controlled-workspace-decision-brief/`, this scenario is evaluated
from a recorded trajectory rather than a live Inspect run: the trace lives
under the top-level `traces/` directory (`coding-bugfix-good.json`,
`coding-bugfix-bad.json`), with its expected verdicts in the top-level
`expected/` directory.
