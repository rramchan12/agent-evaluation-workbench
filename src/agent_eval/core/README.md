# core/

The framework-agnostic layer — the project's actual distinctive
contribution, per [ARCHITECTURE.md §6](../../../ARCHITECTURE.md). Nothing in
here should need to know that Inspect AI exists; it operates purely on a
normalized trajectory.

Planned modules:

- `requirements.py` — the requirement model and hierarchy (outcome,
  obligation, prohibition, verification)
- `evidence.py` — the evidence selector: requirement -> the specific trace
  events/artifacts relevant to it
- `evaluators.py` — the evaluator registry: evaluator ID -> implementation,
  so evaluators can be added without editing existing scenarios or this file
- `reconciliation.py` — deterministic precedence, disagreement handling,
  abstention
- `release.py` — the release policy engine, producing
  `PASS` / `FAIL` / `REVIEW_REQUIRED` / `INSUFFICIENT_EVIDENCE`

If a runtime-neutral kernel is ever extracted (Stage 5 in
[ARCHITECTURE.md](../../../ARCHITECTURE.md)), this is the code that gets
extracted — everything else in this package is Inspect-specific plumbing
around it.
