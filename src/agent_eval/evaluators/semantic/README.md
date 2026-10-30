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

- `fake_judge.py` — Stage 1: a deterministic stand-in with **no real LLM
  call** (keyword/rubric matching over a text source such as an artifact).
  Lets the rest of the pipeline (evidence selection, evaluation,
  reconciliation, release) be tested reproducibly before any real model
  judge is introduced.
- `judge_interface.py` / `real_judge.py` (not yet implemented) — Stage 3:
  the evidence-bounded contract every judge implements, and a real model
  call, to be added only once disagreement handling and evidence bundling
  are proven against the fake judge.
