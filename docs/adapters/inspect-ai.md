# Inspect AI adapter

Status: **removed; candidate for a future adapter.**

The harness never runs Inspect AI or any other agent runtime. An earlier
revision drove Inspect tasks and normalized their eval logs
(`trace/inspect_adapter.py`, `agent-eval run`); that coupling was removed so the
harness only ingests traces (see [ARCHITECTURE.md §0](../../ARCHITECTURE.md)).

Inspect AI remains a legitimate trace source. A new adapter would convert an
Inspect eval log, produced by Inspect outside this harness, into a canonical
`Trajectory`, and `agent-eval evaluate` would then score it like any other
trace.

## Source-specific behavior to preserve

- Resolve Inspect attachment placeholders before reading tool arguments and
  results.
- Preserve tool calls, results, errors, and sample metadata.
- Treat the runtime log as the source of execution truth; evaluators operate
  only after normalization.

See [Authoring an adapter](./authoring.md) for the shared contract.
