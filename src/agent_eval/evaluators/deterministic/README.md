# evaluators/deterministic/

Generic, config-driven checks over trace evidence. No scenario-specific
logic lives here — only capability, configured per requirement.

Planned evaluators:

- `allow_list_policy.py` — a selected field's value must be in (or out of) a
  configured list. Example uses: "only approved document IDs may be read,"
  "writes may only occur under `src/`."
- `temporal_order.py` — event A must precede or follow event B. Example
  uses: "validate after the final write," "tests run after the last edit."
- `reference_validity.py` — every reference (e.g. a citation) must point to
  something the agent actually observed.
- `schema_validation.py` — an artifact must conform to a declared schema.

Each is intentionally reusable across unrelated scenarios; see
[evaluators/README.md](../README.md) for a worked example.
