# Framework Capability Discovery

**Snapshot date:** 2026-11-11  
**Scope:** Microsoft Agent Framework, Google ADK, LangGraph, LangSmith,
Inspect AI, Pydantic Evals, and Promptfoo  
**Method:** Claims were checked against official documentation and canonical
repositories. A missing documented capability is recorded as unknown or custom,
not as proof that the capability cannot exist.

## Classification

- **Native:** available through documented open-source product APIs.
- **Affiliated:** available through the vendor's official companion platform or
  hosted service.
- **Custom:** requires application-specific code or policy.
- **Unknown:** official sources did not establish the behavior.

## Summary

| Framework | Native strength | Stored-run evaluation | Repetition | Stateful execution and HITL | Disagreement and abstention | CI gate | Local without hosted account |
|---|---|---|---|---|---|---|---|
| Microsoft Agent Framework | Agent/workflow runtime, local evaluators, tool checks | Existing responses are native; full trace evaluation uses Foundry | Native | Native checkpoints and approvals | Custom; Foundry has limited `not_applicable` behavior | Native assertions | Yes for deterministic checks |
| Google ADK | Eval sets, tool trajectories, graph workflows | Open-source evaluator reruns the agent; historical trace scoring is hosted or custom | Native | Native graph state and confirmations | Per-metric results; reconciliation is custom | Native CLI and pytest | Basic deterministic metrics |
| LangGraph | Stateful graph runtime, checkpoints, retries, interrupts | Provided by LangSmith, not LangGraph | Custom or LangSmith | Native | Custom | Custom or LangSmith | Yes |
| LangSmith | Datasets, traces, evaluators, experiments | Native evaluation of existing experiments | Native | Human annotation, not runtime approval | Partial; no verified first-class adjudication or abstention policy | Native integrations; policy is custom | Partial |
| Inspect AI | Local evaluation runtime, sandboxes, scorers, logs | Native rescoring of stored logs | Native | Native checkpoints and approvals | Native scorer panels, agreement metrics, and unscored results | Quality thresholds require custom policy | Yes |
| Pydantic Evals | Typed Python evaluations and span evaluators | Native evaluator replay primitive; persistence is custom | Native | Arbitrary Python tasks; workflow engine is custom | Custom; Logfire adds human review | Custom | Yes |
| Promptfoo | Declarative assertions, CI, reports, red teaming | Historical output replay is native; exported trace regrading is unknown | Native | Native sequential conversations | Custom | Native exit codes | Yes |

## Microsoft Agent Framework

- MIT-licensed agent and workflow runtime for Python, .NET, and Go.
- `EvalItem` supports conversations, expected outputs, and expected tool calls.
- Local evaluators cover keywords, tool presence, tool names and arguments, and
  custom functions.
- `num_repetitions` repeats queries for consistency measurement.
- Existing responses can be evaluated locally. Full stored trace evaluation is
  documented through Microsoft Foundry.
- `raise_for_status()` and `AssertAllPassed()` support CI failure.
- No built-in cross-evaluator reconciliation or generic insufficient-evidence
  result was documented.

Sources:

- [Repository and license](https://github.com/microsoft/agent-framework)
- [Evaluation](https://learn.microsoft.com/en-us/agent-framework/agents/evaluation)
- [Observability](https://learn.microsoft.com/en-us/agent-framework/agents/observability)
- [Workflow concepts](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/)
- [Foundry evaluation integration](https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/evaluation/microsoft-foundry)

## Google Agent Development Kit

- Apache-2.0 agent runtime with graph workflows and state management.
- `EvalSet` and `EvalCase` provide a JSON representation for sessions, expected
  responses, initial state, and tool trajectories.
- Deterministic metrics include exact, in-order, and any-order tool trajectory
  checks.
- `num_runs` repeats cases. Some model metrics sample judges repeatedly and use
  majority voting.
- The packaged open-source evaluator reruns the agent. Independent historical
  trace evaluation is provided by Google's hosted Agent Platform or requires
  lower-level custom code.
- No cross-metric disagreement resolver was documented.

Sources:

- [Repository and license](https://github.com/google/adk-python)
- [Evaluation](https://adk.dev/evaluate/)
- [Evaluation criteria](https://adk.dev/evaluate/criteria/)
- [Observability](https://adk.dev/observability/)
- [Graph workflows](https://adk.dev/graphs/)
- [Tool confirmation](https://adk.dev/tools-custom/confirmation/)

## LangGraph

- MIT-licensed stateful workflow runtime, not an evaluation framework.
- Native capabilities include checkpoints, retries, state streaming,
  interrupts, and approval patterns.
- Evaluation datasets, stored-trace experiments, judge execution, and reports
  belong to LangSmith or custom code.

Sources:

- [Overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Fault tolerance](https://docs.langchain.com/oss/python/langgraph/fault-tolerance)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

## LangSmith

- Provides datasets, tracing, deterministic and model evaluators, repeated
  experiments, evaluation of existing experiments, comparisons, annotations,
  and CI integrations.
- LangSmith SDKs are open source. The complete platform server was not verified
  as open source.
- Full self-hosting requires an enterprise license and Kubernetes.
- Multiple evaluators and reviewers are supported, but no first-class
  adjudication statistic or semantic abstention policy was verified.

Sources:

- [Evaluation](https://docs.langchain.com/langsmith/evaluation)
- [Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [Evaluate an existing experiment](https://docs.langchain.com/langsmith/evaluate-existing-experiment)
- [Trajectory evaluation](https://docs.langchain.com/langsmith/trajectory-evals)
- [Repetitions](https://docs.langchain.com/langsmith/repetition)
- [Self-hosting](https://docs.langchain.com/langsmith/self-hosted)

## Inspect AI

- MIT-licensed, fully local evaluation runtime.
- Native tasks, datasets, agents, tools, sandboxes, scorers, logs, viewers,
  repetitions, checkpoints, retries, and approvals.
- `inspect score` applies new scorers to existing logs without rerunning the
  agent.
- Multiple scorers, judge panels, Krippendorff's alpha, and explicit unscored
  results are available.
- A generic built-in trajectory matcher was not identified; custom scorers can
  inspect messages, tools, transcript events, artifacts, and state.
- Score-based release gates require a small custom policy layer.

Sources:

- [Overview](https://inspect.aisi.org.uk/)
- [Tasks](https://inspect.aisi.org.uk/tasks.html)
- [Scoring workflow](https://inspect.aisi.org.uk/scoring-workflow.html)
- [Multiple scorers](https://inspect.aisi.org.uk/multiple-scorers.html)
- [Checkpointing](https://inspect.aisi.org.uk/checkpointing.html)
- [Tool approvals](https://inspect.aisi.org.uk/approval.html)

## Pydantic Evals

- MIT-licensed Python library with typed `Case`, `Dataset`, evaluator, and
  report abstractions.
- Captures OpenTelemetry span trees and includes tool-order, argument, budget,
  deterministic, and model evaluators.
- Evaluators can run over a serialized `EvaluatorContext` and `SpanTree`
  without rerunning the task. The application supplies persistence and
  retrieval.
- Reconciliation, release gates, and evaluator-disagreement handling require
  custom code. Logfire adds optional hosted datasets and human review.

Sources:

- [Pydantic Evals](https://pydantic.dev/docs/ai/evals/evals/)
- [Dataset management](https://pydantic.dev/docs/ai/evals/how-to/dataset-management/)
- [Agentic evaluators](https://pydantic.dev/docs/ai/evals/evaluators/agentic/)
- [Stored-data evaluator reruns](https://pydantic.dev/docs/ai/evals/online-evaluation/#re-running-evaluators-from-stored-data)
- [Multi-run evaluation](https://pydantic.dev/docs/ai/evals/how-to/multi-run/)

## Promptfoo

- MIT-licensed Node CLI/library with a local UI.
- Native YAML and JSON cases, deterministic and model assertions, tool-use
  checks, trajectory sequence checks, repetitions, CI exit codes, and multiple
  report formats.
- Historical outputs can be evaluated through the Echo provider.
- Official documentation did not establish rerunning assertions over an
  exported historical trace.
- Multiple assertions are supported, but disagreement, adjudication, and
  abstention semantics require custom policy.

Sources:

- [Introduction](https://www.promptfoo.dev/docs/intro/)
- [Test cases](https://www.promptfoo.dev/docs/configuration/test-cases/)
- [Assertions](https://www.promptfoo.dev/docs/configuration/expected-outputs/)
- [Tracing](https://www.promptfoo.dev/docs/tracing/)
- [CI/CD](https://www.promptfoo.dev/docs/integrations/ci-cd/)
- [Output formats](https://www.promptfoo.dev/docs/configuration/outputs/)

## Discovery conclusions

1. Inspect AI is the strongest fully local evaluation-runtime baseline in this
   set.
2. MAF and ADK are important vendor-runtime comparisons with native evaluation
   support but different hosted-service boundaries.
3. LangGraph and LangSmith must be measured separately: one is the runtime and
   the other supplies most evaluation-platform capabilities.
4. Pydantic Evals is the lightweight Python baseline.
5. Promptfoo is the declarative and CI-oriented baseline.
6. None of the reviewed systems documents the full project contract as one
   native feature:

```text
requirement -> trajectory evidence -> independent judgments
-> reconciliation -> release decision
```

The benchmark must verify this conclusion rather than assume it.
