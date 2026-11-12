# judge-calibration

Calibration fixture for `agent-eval calibrate` (`core/calibration.py`), not a
scenario: there is no agent, requirement hierarchy, or release policy.

`cases.json` holds hand-labeled evidence bundles and their known-correct
verdicts (`PASS` / `FAIL` / `INSUFFICIENT_EVIDENCE`). Running a judge over
them measures its accuracy before it is trusted in a real scenario. See
`src/agent_eval/evaluators/semantic/README.md` for the case format.
