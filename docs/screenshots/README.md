# docs/screenshots/

PNG screenshots embedded in the top-level README's "GUI" section, captured
by `../../scripts/capture_screenshots.py`:

- `run-complete-pass.png`: Run tab, decision-brief scenario, candidate-2 --
  a clean PASS after a live mockllm evaluation.
- `replay-fail-disagreement.png`: Replay tab, decision-brief scenario, an
  uploaded candidate-1 trajectory -- an overall FAIL, with the
  `approved-sources-only` requirement showing evaluator disagreement (the
  deterministic `forbidden_access` evaluator says FAIL while the semantic
  `grounding-judge-v1` evaluator says PASS).
