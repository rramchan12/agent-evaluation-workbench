# evaluators/semantic/

Model-judged evaluators, behind one evidence-bounded contract
(`judge_interface.py`): given a requirement and a specific evidence bundle
(not the full trajectory), return a verdict, explanation, and evidence
references.

A judge model is a measuring instrument, not part of the system under
test — it must have its own identity, prompt, rubric, and version recorded,
and it must never share a model, credential, or session with the agent being
evaluated (see ARCHITECTURE.md §4.3).

Planned modules:

- `judge_interface.py` — the evidence-bounded contract every judge implements
- `fake_judge.py` — Stage 1: a deterministic stand-in with **no real LLM
  call**, used so the rest of the pipeline (evidence selection, evaluation,
  reconciliation, release) can be tested reproducibly before any real model
  judge is introduced
- `real_judge.py` — Stage 3: a real model call, added only once disagreement
  handling and evidence bundling are proven against the fake judge
