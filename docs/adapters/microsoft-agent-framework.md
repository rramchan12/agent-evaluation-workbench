# Microsoft Agent Framework integration

Microsoft Agent Framework (MAF) is the planned second live runtime integration
and the first portability proof for the workbench's framework-neutral
evaluation core.

The runnable agent and trace-capture experiments live in the separate
[`maf-evaluation-pilot`](https://github.com/rramchan12/maf-evaluation-pilot)
repository. This repository retains the canonical trajectory contract, the
MAF importer, golden trace fixtures, conformance tests, and evaluation reports.

## Integration flow

```text
MAF agent and tools
  -> OpenTelemetry GenAI trace export
  -> dependency-free import_maf.py normalization
  -> canonical Trajectory
  -> existing evidence selection and evaluators
  -> reconciliation and release decision
```

The pilot begins with a scripted chat client and controlled tools so that agent
behavior is reproducible. It produces a pair of traces:

- a valid-process run expected to pass;
- a run that reads a prohibited source but still produces a plausible artifact,
  expected to fail.

This isolates runtime and adapter behavior from live-model variance.

## Repository boundary

The pilot repository owns:

- MAF dependencies and agent construction;
- controlled tools and workspace;
- OpenTelemetry provider/export configuration;
- deterministic trace generation;
- exploratory examples and article walkthroughs.

The workbench owns:

- the canonical `Trajectory` schema;
- `import_maf.py`, which must not require MAF at evaluation time;
- sanitized golden exports and adapter conformance tests;
- requirements, evidence, reconciliation, reports, and CI exit behavior.

## Sensitive telemetry

MAF instrumentation is enabled by default, but prompts, responses, tool
arguments, and tool results may require explicit sensitive-data capture. Enable
that only for controlled pilot data. Never commit credentials or traces
containing unrelated user information.

## Scope

The first integration targets the concrete MAF export produced by the pilot.
A generic OpenTelemetry/OpenInference importer remains deferred until the MAF
mapping has demonstrated which abstractions are actually portable.

See [Authoring an adapter](./authoring.md) and the official
[MAF observability documentation](https://learn.microsoft.com/en-us/agent-framework/agents/observability).
