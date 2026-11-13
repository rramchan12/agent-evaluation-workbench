# Framework Benchmark Plan

**Status:** Planned  
**Based on:** [Framework Capability Discovery](./CAPABILITY_DISCOVERY.md)  
**Targets:** Microsoft Agent Framework, Google ADK, LangGraph, LangSmith,
Inspect AI, Pydantic Evals, and Promptfoo

## Benchmark question

How much native or affiliated framework support is available for this chain,
and how much custom machinery is required?

```text
requirement -> trajectory evidence -> independent judgments
-> reconciliation -> release decision
```

The benchmark will not produce one opaque framework ranking. It will report
capability coverage, custom effort, evidence loss, and operational dependencies
separately.

## Shared simulated application

Extend the existing controlled-workspace scenario with four portable tools:

```text
search_workspace
read_artifact
write_artifact
validate_artifact
```

The benchmark requirements are:

1. Read every required approved source.
2. Do not read the prohibited source.
3. Produce every required report section.
4. Cite only approved evidence observed during the run.
5. Validate the artifact after its final write.
6. Request approval before a designated consequential write.
7. Report failure accurately when completion cannot be proven.

## Canonical traces

Generate these once in the framework-neutral simulator. Every adapter receives
the same trace content and expected requirement verdicts.

| ID | Behavior | Expected release result |
|---|---|---|
| T1 | Correct result and valid process | `PASS` |
| T2 | Correct report after reading a prohibited source | `FAIL` |
| T3 | Valid process but incomplete report | `FAIL` |
| T4 | Validation occurs before the final write | `FAIL` |
| T5 | A required tool event is missing from the trace | `INSUFFICIENT_EVIDENCE` |
| T6 | Write times out after commit; agent rereads state before continuing | `PASS` |
| T7 | Write times out after commit; agent retries blindly | `FAIL` |
| T8 | Consequential write occurs without approval | `FAIL` |
| T9 | Two semantic judges disagree on report quality | `REVIEW_REQUIRED` |
| T10 | The same agent alternates between pass and fail across repetitions | Reliability failure or conditional release |

## Track A: Recorded-trace evaluation

Feed every framework the same canonical traces without rerunning an agent.

Measure:

- whether evaluators can run without agent execution;
- which trace fields survive import and export;
- whether evidence can be linked to individual requirements;
- whether missing evidence stays distinct from a failed requirement;
- whether independent evaluator results remain available after aggregation;
- whether the result can be exported into the harness evidence format.

Discovery-derived checks:

- Inspect AI and LangSmith support stored-run rescoring natively.
- MAF supports existing response evaluation locally; full stored-trace
  evaluation is Foundry-backed.
- Pydantic Evals exposes evaluator replay but leaves storage to the caller.
- ADK's packaged evaluator reruns the agent.
- Promptfoo documents historical output replay, not historical trace regrading.

## Track B: Native scripted execution

Implement the same deterministic behavior in each applicable runtime:

- valid agent;
- process-violation agent;
- outcome-failure agent;
- safe-recovery agent;
- unsafe-recovery agent.

No model is used. This isolates framework behavior from model variance.

Measure:

- framework-specific code and configuration;
- setup time;
- trace completeness;
- state and checkpoint behavior;
- approval, interrupt, and resume behavior;
- repetition behavior;
- wall-clock execution time;
- dependencies, services, and credentials.

LangGraph runtime and LangSmith evaluation receive separate results. MAF and ADK
results also separate open-source behavior from Foundry or Google-hosted
capabilities.

## Track C: Judgment and release policy

Run one deterministic evaluator panel and one fixed fake semantic judge over the
same evidence.

Measure:

- multiple-evaluator support;
- preservation of individual judgments;
- disagreement detection;
- abstention or insufficient-evidence handling;
- deterministic precedence;
- blocker rules;
- CI exit behavior;
- report traceability.

A real model judge is out of scope until framework behavior is measured. It
would add provider and model variance to the initial comparison.

## Capability classification

Every benchmark observation uses one of these factual labels:

- `NATIVE`: works through documented open-source product APIs.
- `AFFILIATED`: requires the vendor's official companion platform or service.
- `ADAPTER`: requires a bounded format or API adapter.
- `CUSTOM`: requires application-specific implementation.
- `UNSUPPORTED`: documented APIs cannot implement the case.
- `UNKNOWN`: official sources do not establish the behavior.

Do not convert these labels into a weighted score.

## Quantitative measurements

Record:

- framework-specific lines of code;
- configuration-file count;
- setup duration;
- external-service count;
- credentials required;
- execution duration;
- trace fields retained and lost;
- custom evaluator count;
- custom reconciliation-rule count;
- custom release-policy-rule count.

## Framework-specific hypotheses

| Framework | Capability to verify | Gap to test |
|---|---|---|
| Microsoft Agent Framework | Local evaluators, repetitions, workflows, CI assertions | Trace replay without Foundry; disagreement and abstention |
| Google ADK | Formal eval sets and tool-trajectory metrics | Evaluator-only replay and cross-metric reconciliation |
| LangGraph | Stateful execution, retries, checkpoints, interrupts | Evaluation requires LangSmith or custom code |
| LangSmith | Stored-trace experiments and comparisons | Hosted dependency, adjudication, abstention |
| Inspect AI | Local execution, rescoring, repetitions, scorer panels | Requirement hierarchy and release gates need an extension |
| Pydantic Evals | Typed lightweight evaluation and span checks | Persistence, reconciliation, and CI gates need glue |
| Promptfoo | Declarative tests, reports, and CI behavior | Full historical trace replay and requirement evidence |

These are hypotheses from discovery, not benchmark results.

## Execution order

1. Freeze the benchmark requirement set and normalized trace schema.
2. Generate T1-T10 once through the existing framework-neutral simulator.
3. Record expected requirement and release verdicts as benchmark ground truth.
4. Implement Inspect AI recorded-log rescoring as the current baseline.
5. Implement Pydantic Evals as the lightweight local comparison.
6. Implement MAF and ADK native execution comparisons.
7. Implement LangGraph execution and evaluate its traces through LangSmith as a
   separate layer.
8. Implement Promptfoo as the declarative CI comparison.
9. Run the fixed judgment and release-policy cases.
10. Publish the evidence matrix, implementation-effort report, trace-loss
    report, and adoption decision.

## Benchmark outputs

The completed benchmark produces:

1. a capability matrix with evidence for every classification;
2. framework-specific adapters or reproductions;
3. verdict comparison for T1-T10;
4. trace import/export loss reports;
5. native versus custom implementation counts;
6. local versus hosted dependency boundaries;
7. setup and runtime measurements;
8. a recommendation for each framework.

Each framework receives one of these recommendations:

- **Base runtime:** build the harness as an extension of it.
- **Evaluation adapter:** consume or produce its cases, traces, or scores.
- **Scorer provider:** reuse selected evaluators only.
- **Design reference:** borrow patterns without adding a dependency.
- **Exclude from MVP:** integration cost exceeds demonstrated value.

## Completion criteria

The benchmark is complete when:

- all ten canonical traces have ground-truth verdicts;
- every target has a factual capability result or an explicit `UNKNOWN`;
- framework-native and custom behavior are reported separately;
- LangGraph and LangSmith are reported separately;
- open-source and hosted vendor capabilities are reported separately;
- trace loss is measured rather than inferred;
- the final adoption decision links back to benchmark evidence.
