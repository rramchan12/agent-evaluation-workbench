# evaluators/deterministic/

Generic, config-driven checks over trace evidence. No scenario-specific
logic lives here — only capability, configured per requirement.

Implemented in `checks.py`, registered by ID in `core/evaluators.py`:

- `required_inspection` — every value in a configured list must appear in a
  chosen argument field across the evidence bundle (e.g. "every approved
  doc_id was read", "the failing test file was read").
- `forbidden_access` — no event in the evidence bundle may have a chosen
  argument field matching a configured forbidden value (e.g. "the
  unapproved document was never read", "the test file was never edited").
- `verify_after_last_write` — finds the last event for a configured write
  tool and requires a successful event for a configured verify tool to
  occur afterward (e.g. "validated after the final write", "tests rerun
  after the last edit").
- `last_result_matches` — the last event for a configured tool must have a
  configured result field equal to a configured value (e.g. "the last test
  run passed").
- `artifact_sections` — a configured artifact (or the final output, if no
  artifact key is given) must contain every configured required section
  heading.
- `citations_observed` — every citation found in an artifact (via a
  configured regex) must correspond to a value actually observed through a
  configured argument field in the evidence bundle.

Each is intentionally reusable across unrelated scenarios; see
[evaluators/README.md](../README.md) for a worked example.
