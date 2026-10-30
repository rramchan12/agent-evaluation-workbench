# evaluators/

Evaluators are **generic and config-driven**, not scenario-specific code.
Each one is registered once, by ID, in `core/evaluators.py`'s registry.
A scenario's `requirements.yaml` never introduces new evaluator code — it
only references an evaluator ID and supplies configuration.

This is what makes the project a framework rather than a bundle of one-off
scripts: the same `forbidden_access` evaluator, for example, can check
"the unapproved document was never read" in a decision-brief scenario and
"the protected test file was never edited" in a coding-agent scenario, with
zero new code — only different config.

- [deterministic/](./deterministic/README.md) — rule- and evidence-based checks
- [semantic/](./semantic/README.md) — model-judged checks, behind an
  evidence-bounded contract
