# evaluators/

Evaluators are **generic and config-driven**, not scenario-specific code.
Each one is registered once, by ID, in `core/evaluators.py`'s registry.
A scenario's `requirements.yaml` never introduces new evaluator code — it
only references an evaluator ID and supplies configuration.

This is what makes the project a framework rather than a bundle of one-off
scripts: the same `allow_list_policy` evaluator, for example, can check
"only approved sources were read" in a Cowork-style scenario and "no writes
outside src/" in a Copilot-style scenario, with zero new code — only
different config.

- [deterministic/](./deterministic/README.md) — rule- and evidence-based checks
- [semantic/](./semantic/README.md) — model-judged checks, behind an
  evidence-bounded contract
