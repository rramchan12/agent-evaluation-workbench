# evaluators/semantic/

Model-judged evaluators, behind one evidence-bounded contract
(`judge_interface.py`): given a requirement and a specific evidence bundle
(not the full trajectory), return a verdict, explanation, and evidence
references.

A judge model is a measuring instrument, not part of the system under
test — it must have its own identity, prompt, rubric, and version recorded,
and it must never share a model, credential, or session with the agent being
evaluated (see ARCHITECTURE.md §4.3).

Modules:

- `judge_interface.py` — the shared contract every judge implements:
  `JUDGE_VERDICTS` (`PASS` / `FAIL` / `INSUFFICIENT_EVIDENCE` — a single
  judge never emits `REVIEW_REQUIRED`; only reconciliation or a human
  produces that), `text_source(bundle, source)` to pull the right text out
  of an evidence bundle, and `parse_judge_response(raw)`, which never
  raises — malformed JSON, a non-dict payload, or an unrecognized verdict
  all fall back to `INSUFFICIENT_EVIDENCE` rather than crashing the run.
- `fake_judge.py` — Stage 1: a deterministic stand-in with **no real LLM
  call** (keyword/rubric matching over a text source such as an artifact).
  Lets the rest of the pipeline (evidence selection, evaluation,
  reconciliation, release) be tested reproducibly before any real model
  judge is introduced.
- `real_judge.py` — Stage 3: a real model judge, registered as the
  `real_judge` semantic evaluator. Calls Inspect AI's `get_model(...)` and
  `Model.generate(...)` (wrapped in `asyncio.run`, since no event loop is
  running in the CLI/test callers) and parses the response through
  `judge_interface.parse_judge_response`. Config keys:
  - `model` — the Inspect AI model identifier to use (see
    `_resolve_model_name` for defaults/fallback).
  - `min_confidence` — optional float; if the parsed confidence is below
    this threshold, the judge abstains (`INSUFFICIENT_EVIDENCE`) instead
    of returning its raw verdict.
  - `mock_responses` — a list of scripted raw JSON response strings,
    consumed in order via Inspect AI's `mockllm` provider. This is the
    sanctioned way to get deterministic, no-API-key test and calibration
    runs; **it must never be set in a production scenario's evaluator
    config** — only in tests and `scenarios/judge-calibration/cases.json`.

Judge calibration (`core/calibration.py`, `agent-eval calibrate`) scores a
judge's verdicts against a hand-labeled fixture
(`scenarios/judge-calibration/cases.json`) to catch rubric or prompt drift
before it reaches a real scenario run.
