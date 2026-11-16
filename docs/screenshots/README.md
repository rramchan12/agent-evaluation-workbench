# docs/screenshots/

PNG screenshots embedded in the top-level README's "GUI" section, captured
by `../../scripts/capture_screenshots.py`:

- `replay-pass.png`: Replay tab, decision-brief scenario, the recorded
  `decision-brief-candidate-2` trace -- a clean PASS.
- `replay-fail-disagreement.png`: Replay tab, decision-brief scenario, the
  recorded `decision-brief-candidate-1` trace, uploaded -- an overall FAIL, with the
  `approved-sources-only` requirement showing evaluator disagreement (the
  deterministic `forbidden_access` evaluator says FAIL while the semantic
  `grounding-judge-v1` evaluator says PASS).
