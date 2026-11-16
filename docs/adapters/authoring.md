# Authoring a runtime adapter

An adapter converts one source run into one canonical `Trajectory`. The
contract is defined by
[`Event` and `Trajectory`](../../src/agent_eval/trace/model.py); this document
states the behavioral requirements that are not obvious from the Python
dataclasses alone.

## Required trajectory fields

- `trajectory_id`: stable identity for this captured run.
- `scenario_id`: scenario evaluated by the workbench.
- `system_under_test`: agent, model, configuration, or build identity.
- `events`: observable execution steps in source order.
- `complete`: whether the importer knows the record is complete.

`final_output`, `artifacts`, timestamps, and metadata are optional only when the
source genuinely does not provide them. Absence must not be replaced with
invented values.

## Event mapping

Assign sequential canonical IDs (`e0`, `e1`, ...) after establishing source
order. Preserve source IDs in `metadata` when available.

For tool activity, map:

| Canonical field | Source evidence |
|---|---|
| `kind` | Usually `tool_call`; use another stable kind for messages or scores |
| `name` | Tool or function name |
| `arguments` | Decoded call arguments |
| `result` | Tool result without lossy stringification where possible |
| `error` | Explicit error text or structured source error |
| `timestamp` | Source timestamp in an unambiguous format |
| `metadata` | Trace/span IDs, runtime event type, status, and source extensions |

Keep a failed tool call as an event. Never drop it because it has no successful
result.

## Ordering and correlation

The canonical event list must reflect observable execution order. If the source
uses nested spans, document the ordering rule used to flatten them. Preserve
trace IDs, span IDs, parent span IDs, call IDs, and message IDs in metadata so
the original structure remains recoverable.

If ordering cannot be established reliably, set `complete` to `false` and give
an `incompleteness_reason`.

## Completeness and missing evidence

`complete=false` is required when the importer knows that the export was
truncated, spans were dropped, capture began late, the run aborted before
records were flushed, or required attachments could not be resolved.

Do not translate missing evidence into a passing empty event list. The harness
uses completeness to distinguish `INSUFFICIENT_EVIDENCE` from a verified
requirement failure.

## Artifacts and final output

Populate `final_output` from the terminal assistant response when one is
unambiguous. Populate `artifacts` from captured final artifact contents, not
merely file names. If the source records writes but not final state, retain the
write events and leave `artifacts` empty.

## Provenance and redaction

Trajectory metadata should identify:

- source runtime and version;
- adapter name and version;
- source trace or export format version;
- capture configuration relevant to evidence availability;
- redaction or sensitive-data settings;
- original trace ID and source file hash when available.

Adapters must preserve existing redaction. They must not enable sensitive
telemetry implicitly or place credentials, tokens, or unrelated user data in
fixtures.

## Conformance tests

Every adapter should test:

1. stable source ordering and sequential canonical IDs;
2. tool arguments, results, and failures;
3. final output and artifacts;
4. provenance metadata;
5. truncated or incomplete input;
6. malformed required fields with explicit errors;
7. at least one end-to-end scenario replay;
8. equivalent requirement verdicts for equivalent canonical evidence.

Golden fixtures should be small, sanitized, versioned, and attributable to the
source runtime version that produced them.
