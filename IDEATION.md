# Open Agent Evaluation Harness

## Why We Are Building It This Way

**Status:** Design rationale and source review  
**Date:** 2026-09-12  
**Companion document:** [ARCHITECTURE.md](./ARCHITECTURE.md) contains the system design, roadmap, data model, and reference scenarios. This document records the research and engineering choices behind it.  
**Source check:** We checked each project and paper against its repository, official documentation, or arXiv page on 2026-09-12. Section 7 lists the sources.

---

## The short version

Most agent evaluations answer one question: did the final answer or state look right?

That is necessary, but it is not enough. An agent can pass a test after using the wrong tool, skipping a required check, retrying a write blindly, or crossing a policy boundary. Looking only at the result hides those failures.

Model judges do not fix this on their own. They are useful for semantic checks, but published work documents order bias, self-preference, inconsistent grading, and missed trajectory faults.

We are building the layer between execution and release:

```text
declared requirement
    -> events and artifacts from the run
    -> independent evaluator results
    -> reconciled verdict
    -> release decision
```

The harness will not replace agent runtimes, domain benchmarks, or tracing products. It will connect them. We will extend an existing execution runtime, store requirement-linked evidence in a portable contract, and let evaluators run again without rerunning the agent.

---

## 1. Terms we use

Papers and projects use these terms differently. These are the definitions used in this repository.

| Term | Working definition |
|---|---|
| **Agent trajectory** | The ordered sequence of an agent's messages, tool calls, tool results, and artifact changes during one run, as distinct from only its final response. |
| **Outcome evaluation** | Judging a run by its final state or answer alone (for example, did the tests pass, does the final document match a reference). |
| **Process / trajectory evaluation** | Judging a run by the steps that produced the outcome (ordering, tool use, intermediate milestones, policy compliance), independent of whether the final state was reached. |
| **LLM-as-judge** | Using a language model to score or compare outputs, introduced and studied at scale by [Zheng et al., 2023](https://arxiv.org/abs/2306.05685). |
| **Agent-as-judge** | Using an agentic system — one that can inspect artifacts, run tests, and gather evidence — as the evaluator, introduced by [Zhuge et al., 2024](https://arxiv.org/abs/2410.10934). |
| **Requirement** | A discrete, evaluable expectation of a task (an outcome, an obligation, a prohibition, or a verification step), as opposed to a single scalar task score. |
| **Evidence** | The specific trace events, tool results, or artifacts that support a given evaluator's verdict on a given requirement. |
| **Reconciliation** | The declared procedure for combining multiple evaluators' judgments on the same requirement into one verdict, particularly when they disagree. |
| **Release decision** | The final PASS / FAIL / REVIEW_REQUIRED / INSUFFICIENT_EVIDENCE outcome derived from reconciled requirement verdicts and an explicit policy. |
| **Calibration** | Measuring an evaluator's own accuracy, bias, and failure modes against a human-labeled reference set, rather than assuming it is correct because it is capable. |
| **Abstention** | An evaluator or the harness declining to assert PASS or FAIL when available evidence cannot support either conclusion. |
| **Deterministic evaluator** | An evaluator whose verdict is produced by code, rules, or tests rather than model inference. |
| **Semantic evaluator** | An evaluator whose verdict depends on a model's judgment of meaning, quality, or intent satisfaction. |
| **Replay** | Re-running evaluators against a previously recorded trajectory without re-executing the agent. |

---

## 2. What we learned from the research

We reviewed the main evaluation patterns that affect this build. [Survey on Evaluation of LLM-based Agents](https://arxiv.org/abs/2503.16416) provides a broader literature review; the notes below focus on decisions we need to make in the harness.

### 2.1 Agents need environments, not answer keys

[AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688) evaluates models as actors in operating systems, databases, knowledge graphs, games, and web environments. That distinction matters here: the harness must record actions and state changes, not just text.

### 2.2 Existing environments already solve execution

We do not need to build another coding, browser, desktop, or tool-use environment:

- [SWE-bench](https://arxiv.org/abs/2310.06770) established repository-level code repair evaluated against executable tests on real GitHub issues.
- [SWE-agent](https://arxiv.org/abs/2405.15793) showed that the agent-computer interface itself — not only the underlying model — materially affects coding-agent performance.
- [WebArena](https://arxiv.org/abs/2307.13854) introduced self-hosted, resettable websites with execution-based task verification.
- [OSWorld](https://arxiv.org/abs/2404.07972) extended execution-based verification to cross-application desktop tasks in virtual machines.
- [AppWorld](https://arxiv.org/abs/2407.18901) introduced controllable synthetic applications with state-difference evaluation across task variations.
- [ToolSandbox](https://arxiv.org/abs/2408.04682) added stateful tools, an on-policy user simulator, and dynamic evaluation of both intermediate and final milestones.
- [RoTBench](https://arxiv.org/abs/2401.08326) studied robustness by injecting controlled noise into tool selection, parameters, and observations.
- [tau-bench](https://arxiv.org/abs/2406.12045) evaluated tool-agent-user interaction jointly against final database state and policy adherence, introducing pass-to-the-power-k as a reliability measure across repeated trials.
- [tau-squared-bench](https://arxiv.org/abs/2506.07982) extended this to a dual-control environment where both agent and user act on shared state.

These projects show how to reset environments, execute tasks, and verify state. We can reuse those ideas and runtimes. Our work starts where their outcome checks stop: linking the recorded path to explicit requirements.

### 2.3 Task success and policy compliance are separate

Three projects make the separation clear:

- [SOPBench](https://arxiv.org/abs/2503.08669) separates goal completion from procedural compliance, representing obligations, prohibitions, and ordering constraints as rules distinct from task success.
- [AgentDojo](https://arxiv.org/abs/2406.13352) treats tool output as an untrusted security boundary, evaluating utility and prompt-injection security independently.
- [AgentHarm](https://arxiv.org/abs/2410.09024) evaluates whether harmful multi-step objectives are actually executed through tools, not merely whether an initial textual response refuses.

### 2.4 Model judges are inputs, not authorities

Open-ended tasks need semantic judgment. The evidence also says not to trust one model judge:

- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) established LLM-as-judge as a scalable evaluation method while documenting position, verbosity, and self-enhancement bias.
- [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926) showed that swapping candidate order can flip a judge's verdict, arguing for order-randomized or bidirectional judging.
- [Replacing Judges with Juries](https://arxiv.org/abs/2404.18796) showed that panels of diverse, often smaller, models can reduce single-judge bias and cost.
- [JudgeBench](https://arxiv.org/abs/2410.12784) introduced objectively grounded difficult cases for calibrating judges, rather than relying only on human preference agreement.

### 2.5 The trace is part of the result

The following work directly informs our requirement and evidence model:

- [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) showed, in mathematical reasoning, that supervising intermediate steps can outperform supervising only final answers. Its domain is not tool-use agents, so it is treated here as motivating evidence for process supervision as a principle, not as a transferable method.
- [Agent-as-a-Judge: Evaluate Agents with Agents](https://arxiv.org/abs/2410.10934) proposed agentic evaluators that inspect intermediate artifacts and behavior against hierarchical requirements, reporting stronger reliability than plain LLM-as-judge on its DevAI benchmark of 55 development tasks with 365 hierarchical requirements.
- [PaperBench: Evaluating AI's Ability to Replicate AI Research](https://arxiv.org/abs/2504.01848) used versioned hierarchical rubrics with objective evidence and separately benchmarked its own automated judge, rather than assuming the judge's competence.
- [AgentBoard: An Analytical Evaluation Board of Multi-turn LLM Agents](https://arxiv.org/abs/2401.13178) introduced fine-grained progress and milestone tracking because terminal success alone reveals little about how an agent got there.
- [AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories](https://arxiv.org/abs/2504.08942) benchmarked automatic trajectory graders against human labels across multiple behavioral dimensions, finding that no single grader is uniformly reliable.

### 2.6 Recent work we are watching

Several 2026 preprints tackle silent trajectory faults directly. They are relevant, but too new to treat as established results:

- [AgentEval: DAG-Structured Step-Level Evaluation for Agentic Workflows with Error Propagation Tracking](https://arxiv.org/abs/2604.23581) proposes modeling workflow steps and dependencies explicitly enough to localize the first divergence in a failing run.
- [trajectory-judge: What Outcome-Only LLM Judges Miss on Agent Trajectories](https://arxiv.org/abs/2609.00038) uses controlled fault injection to show that outcome-only judges miss constructed process faults, and that step-level rubrics improve but do not eliminate this blindness.
- [AgentLens: Revealing the Lucky Pass Problem in SWE-Agent Evaluation](https://arxiv.org/abs/2605.12925) shows that passing coding-agent trajectories can still contain blind retries, regressions, and missing verification — a "lucky pass" that outcome-based benchmarks such as SWE-bench cannot distinguish from a sound trajectory.
- [Grounded Checklist Partial Credit for Agent Skill Trajectories](https://arxiv.org/abs/2608.27487) proposes evidence-grounded checklist scoring with explicit abstention when the trace cannot support a conclusion, keeping deterministic verification separate from judge output.
- [LLM-as-a-Judge Is Not an Oracle: Why Self-Improving Agents Need Deterministic Guardrails](https://arxiv.org/abs/2609.02246) argues, as a position and case-study paper, that semantic judges must remain subordinate to hermetic execution and deterministic acceptance checks.
- [Workflow Cards: Structured Summaries of Workflow Executions Using Provenance Data](https://arxiv.org/abs/2608.11022) proposes structured, execution-level provenance summaries as a reporting format for workflow runs.

Our takeaway is practical: keep deterministic checks, preserve every judge result, point each judgment to evidence, and return "insufficient evidence" instead of forcing a score.

---

## 3. What each evaluator is good for

Each evaluator type covers a different part of the run:

| Approach | What it measures | Representative work | Principal blind spot |
|---|---|---|---|
| Outcome evaluation | Final state or answer correctness | SWE-bench, WebArena, OSWorld, tau-bench (final state) | Cannot distinguish a sound trajectory from a "lucky pass" ([AgentLens](https://arxiv.org/abs/2605.12925)) |
| Process / trajectory evaluation | Intermediate steps, milestones, ordering, policy compliance | AgentBoard, SOPBench, AgentEval | Requires an explicit model of expected steps, which is costly to author and may not generalize across tasks |
| LLM-as-judge | Semantic quality, intent satisfaction, response comparison | MT-Bench/Arena paper, PaperBench | Subject to order, verbosity, and self-enhancement bias ([Fair Evaluators](https://arxiv.org/abs/2305.17926)) |
| Agent-as-judge | Artifact inspection, test execution, requirement-level findings | Agent-as-a-Judge | Costly, can share blind spots with the evaluated agent, needs isolation |
| Policy / safety evaluation | Whether prohibited or unauthorized behavior occurred | AgentDojo, AgentHarm, SOPBench | Typically evaluated separately from task success rather than integrated into one verdict |
| Human evaluation | Ground truth for calibrating the above | AgentRewardBench's human-labeled trajectories | Expensive and slow; unsuitable as the default evaluator |

We will compose these evaluators rather than pick one. The unresolved engineering problem is how to combine their results without hiding disagreement.

---

## 4. What we can reuse

These are the projects and standards we checked before drawing the system boundary. Final adoption choices are in [ARCHITECTURE.md](./ARCHITECTURE.md).

### 4.1 Standards and interchange formats

| Foundation | Verified capability |
|---|---|
| [OpenTelemetry](https://opentelemetry.io/) and [OTLP](https://github.com/open-telemetry/opentelemetry-proto) | Vendor-neutral trace model, context propagation, transport, spans, events, and metrics |
| [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai) | Emerging vocabulary for GenAI client, agent/tool, and MCP telemetry; still evolving and not yet stable |
| [OpenInference](https://github.com/Arize-ai/openinference) | Established OpenTelemetry-based semantic conventions for LLM, agent, tool, retrieval, and evaluator spans |
| [JSON Schema 2020-12](https://json-schema.org/specification) | Standard schema/validation format for records crossing process or framework boundaries |
| [Model Context Protocol](https://github.com/modelcontextprotocol/modelcontextprotocol) | Versioned, JSON-RPC-based protocol for hosts, clients, servers, tools, resources, and prompts |

Multi-agent protocols such as A2A are out of scope for the first build. We need to get single-agent trajectory evaluation right before adding coordination semantics.

### 4.2 Execution and agent runtimes

| Project | Verified capability |
|---|---|
| [Inspect AI](https://inspect.aisi.org.uk/) | Tasks and datasets, agents and agent bridges, tools, extensible sandboxes, approvals, checkpointing, scorers, evaluation logs, and viewers; [MIT-licensed](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/LICENSE) |
| [Harbor](https://github.com/harbor-framework/harbor) | Container-environment harness for evaluating arbitrary coding/terminal agents, including Terminal-Bench 2 and supported third-party datasets; [Apache-2.0](https://github.com/harbor-framework/harbor/blob/main/LICENSE) |
| [Google ADK evaluation](https://adk.dev/evaluate/) | Session-derived eval cases, expected tool-trajectory matching, response/rubric/safety/model-based criteria; this is rerun-and-compare evaluation, not evaluator-only replay of an immutable execution |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) | Agent, harness-agent, and graph/functional workflow runtime with model, MCP, middleware, hosting, and observability integrations |

### 4.3 Evaluator and evaluation libraries

| Project | Verified capability |
|---|---|
| [Pydantic Evals](https://ai.pydantic.dev/evals/) | Typed cases and datasets, custom/built-in evaluators, execution reports, OpenTelemetry-instrumented evaluation |
| [DeepEval](https://github.com/confident-ai/deepeval) | Pytest-style LLM application evaluation with response, retrieval, conversational, and agent-oriented metrics |
| [Azure AI Evaluation](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/evaluation/azure-ai-evaluation) | Callable NLP, model-assisted quality, retrieval, safety, composite, and custom evaluators |
| [Invariant Guardrails](https://github.com/invariantlabs-ai/invariant) | Rule-based guardrails for LLM/MCP traffic, including policies over supported message and tool-call traces |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | Declarative tests/assertions, providers, CI integration, and red teaming; MIT-licensed, now owned by OpenAI |
| [OpenAI Evals](https://github.com/openai/evals) | Open-source eval registry and model-graded evaluation framework; current OpenAI guidance emphasizes hosted Dashboard/API Evals over this repository |

### 4.4 Domain benchmarks and environments

The relevant domain benchmarks are [AgentBench](https://arxiv.org/abs/2308.03688), [SWE-bench](https://arxiv.org/abs/2310.06770), [SWE-agent](https://arxiv.org/abs/2405.15793), [WebArena](https://arxiv.org/abs/2307.13854), [OSWorld](https://arxiv.org/abs/2404.07972), [AppWorld](https://arxiv.org/abs/2407.18901), [ToolSandbox](https://arxiv.org/abs/2408.04682), [RoTBench](https://arxiv.org/abs/2401.08326), [tau-bench](https://arxiv.org/abs/2406.12045), [tau-squared-bench](https://arxiv.org/abs/2506.07982), [AgentDojo](https://arxiv.org/abs/2406.13352), and [AgentHarm](https://arxiv.org/abs/2410.09024). [BrowserGym](https://github.com/ServiceNow/BrowserGym) and [AgentLab](https://github.com/ServiceNow/AgentLab) provide browser environments and experiment tooling.

We can run scenarios in these environments rather than reproducing them. The harness adds a common requirement, evidence, and reconciliation contract above their domain-specific verdicts.

### 4.5 Observability and experiment platforms

| Project | Verified capability | Governance note |
|---|---|---|
| [MLflow GenAI](https://mlflow.org/docs/latest/genai/) | OpenTelemetry-compatible tracing, evaluation, scorers, prompt management, monitoring, storage, UI | — |
| [Langfuse](https://github.com/langfuse/langfuse) | Tracing, sessions, datasets, experiments, prompts, code/model/manual evaluation | Core repository is MIT; identified enterprise directories use a separate license |
| [Phoenix](https://github.com/Arize-ai/phoenix) | OpenInference-based tracing, datasets, experiments, evaluations, prompt tools | Server code is licensed under Elastic License 2.0 — source-available, but not OSI-approved open source |

---

## 5. The missing layer

We compared the existing approaches against six capabilities needed for requirement-level trajectory evaluation:

| Property | Outcome benchmarks | Process/trajectory research | Judge-reliability research | Observability platforms |
|---|---|---|---|---|
| Hierarchical requirements with precedence | Not modeled | Partially modeled (SOPBench, Agent-as-a-Judge's DevAI rubric) | Not modeled | Not modeled |
| Event-addressable evidence | Implicit in test logs | Emerging (Grounded Checklist Partial Credit) | Not the focus | Present as raw spans, not requirement-linked |
| Preserved independent judgments (not averaged) | Not applicable | Rare | Argued for (Replacing Judges with Juries) | Application policy, not a platform feature |
| Explicit deterministic-over-semantic precedence | Implicit (tests are authoritative) | Not standardized | Argued for (LLM-as-a-Judge Is Not an Oracle) | Not enforced |
| Evaluator-only replay of an immutable trajectory | Not designed for this | Not designed for this | Not designed for this | Traces are stored, but replay is not evaluator-scoped |
| Auditable release decision derived from verdicts | CI pass/fail only | Not addressed | Not addressed | Application-specific dashboards, not a portable contract |

We did not find one project that implements all six as a single contract. That claim is limited to the sources and versions checked on 2026-09-12; we will verify it again before publishing.

---

## 6. What we are building

### 6.1 The product boundary

The missing piece is not another benchmark or metric. It is the layer that connects requirements, traces, judgments, and release policy:

```text
declared requirement
    -> relevant trajectory evidence
    -> independent evaluator judgments
    -> reconciled verdict (with disagreement preserved)
    -> auditable release decision
```

The harness answers one question:

> Did this agent satisfy the declared requirements through an acceptable, evidenced process, and does the evidence support release?

### 6.2 Four rules for the build

These rules define the product:

1. **Evaluate requirements, not one aggregate score.** Store a requirement-to-evidence-to-verdict chain for every run.
2. **Keep judgments separate.** Retain deterministic, semantic, and human results before reconciliation. Never hide disagreement in an average.
3. **Let facts win.** When a test, state assertion, or policy rule fully covers a requirement, a model judge cannot overrule it.
4. **Do not guess.** Missing or weak evidence produces `INSUFFICIENT_EVIDENCE` or `REVIEW_REQUIRED`, not a pass.

### 6.3 What we will not build

We will not build another agent runtime, domain benchmark, hosted tracing service, or general policy engine. Those products already exist. We will integrate them.

The scope test for every feature is:

> Does this help prove whether a tool-using agent satisfied a declared requirement through an acceptable and evidenced trajectory? If not, it belongs to an existing runner, domain harness, or observability product, not to this project.

### 6.4 Build path

We considered three approaches:

- **Build inside an existing runner.** This gets to a working demo fastest, but ties the data model to that runner.
- **Build a neutral core and plug runners into it.** This gives us clean boundaries, but creates a real risk of rebuilding execution and tracing.
- **Publish a specification first.** This is clean on paper, but it gives us no working system to test the contract against.

We will extend an actively maintained, permissively licensed runtime instead of replacing one. Where its public extension points are insufficient, we will make focused upstream contributions.

We will extract a runtime-neutral contract only after running real trajectories in at least two domains: one research/artifact task and one software task. That sequence keeps the abstraction grounded in working code.

The roadmap, canonical model, reference scenarios, and selected runtime are in [ARCHITECTURE.md](./ARCHITECTURE.md).

### 6.5 The bet

Existing runners execute agents. Benchmarks check outcomes. Observability tools display traces.

We are connecting those pieces so a team can decide whether an agent is ready to release—and trace that decision back to requirements and evidence.

---

## 7. References

### 7.1 Research papers

**Foundational and outcome-grounded benchmarks**

- [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688)
- [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770)
- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://arxiv.org/abs/2405.15793)
- [WebArena: A Realistic Web Environment for Building Autonomous Agents](https://arxiv.org/abs/2307.13854)
- [OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments](https://arxiv.org/abs/2404.07972)
- [AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents](https://arxiv.org/abs/2407.18901)
- [ToolSandbox: A Stateful, Conversational, Interactive Evaluation Benchmark for LLM Tool Use Capabilities](https://arxiv.org/abs/2408.04682)
- [RoTBench: A Multi-Level Benchmark for Evaluating the Robustness of Large Language Models in Tool Learning](https://arxiv.org/abs/2401.08326)
- [tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains](https://arxiv.org/abs/2406.12045)
- [tau-squared-bench: Evaluating Conversational Agents in a Dual-Control Environment](https://arxiv.org/abs/2506.07982)

**Safety and policy boundaries**

- [SOPBench: Evaluating Language Agents at Following Standard Operating Procedures and Constraints](https://arxiv.org/abs/2503.08669)
- [AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents](https://arxiv.org/abs/2406.13352)
- [AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents](https://arxiv.org/abs/2410.09024)

**LLM-as-judge and judge reliability**

- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)
- [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926)
- [Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models](https://arxiv.org/abs/2404.18796)
- [JudgeBench: A Benchmark for Evaluating LLM-based Judges](https://arxiv.org/abs/2410.12784)

**Process and trajectory evaluation**

- [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050)
- [Agent-as-a-Judge: Evaluate Agents with Agents](https://arxiv.org/abs/2410.10934)
- [PaperBench: Evaluating AI's Ability to Replicate AI Research](https://arxiv.org/abs/2504.01848)
- [AgentBoard: An Analytical Evaluation Board of Multi-turn LLM Agents](https://arxiv.org/abs/2401.13178)
- [AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories](https://arxiv.org/abs/2504.08942)

**Recent convergence (2026 preprints, unreplicated)**

- [AgentEval: DAG-Structured Step-Level Evaluation for Agentic Workflows with Error Propagation Tracking](https://arxiv.org/abs/2604.23581)
- [trajectory-judge: What Outcome-Only LLM Judges Miss on Agent Trajectories](https://arxiv.org/abs/2609.00038)
- [AgentLens: Revealing the Lucky Pass Problem in SWE-Agent Evaluation](https://arxiv.org/abs/2605.12925)
- [Grounded Checklist Partial Credit for Agent Skill Trajectories](https://arxiv.org/abs/2608.27487)
- [LLM-as-a-Judge Is Not an Oracle: Why Self-Improving Agents Need Deterministic Guardrails](https://arxiv.org/abs/2609.02246)
- [Workflow Cards: Structured Summaries of Workflow Executions Using Provenance Data](https://arxiv.org/abs/2608.11022)

**Landscape synthesis**

- [Survey on Evaluation of LLM-based Agents](https://arxiv.org/abs/2503.16416)

### 7.2 Projects, standards, and documentation

**Standards and interchange**

- [OpenTelemetry](https://opentelemetry.io/) / [OTLP](https://github.com/open-telemetry/opentelemetry-proto)
- [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)
- [OpenInference](https://github.com/Arize-ai/openinference)
- [JSON Schema 2020-12](https://json-schema.org/specification)
- [Model Context Protocol](https://github.com/modelcontextprotocol/modelcontextprotocol)

**Execution and agent runtimes**

- [Inspect AI](https://inspect.aisi.org.uk/) ([extension points](https://inspect.aisi.org.uk/extensions/index.html), [MIT license](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/LICENSE))
- [Harbor](https://github.com/harbor-framework/harbor) ([Apache-2.0 license](https://github.com/harbor-framework/harbor/blob/main/LICENSE))
- [Google ADK evaluation](https://adk.dev/evaluate/)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)

**Evaluator and evaluation libraries**

- [Pydantic Evals](https://ai.pydantic.dev/evals/)
- [DeepEval](https://github.com/confident-ai/deepeval)
- [Azure AI Evaluation](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/evaluation/azure-ai-evaluation)
- [Invariant Guardrails](https://github.com/invariantlabs-ai/invariant)
- [Promptfoo](https://github.com/promptfoo/promptfoo)
- [OpenAI Evals](https://github.com/openai/evals)

**Domain environments**

- [BrowserGym](https://github.com/ServiceNow/BrowserGym)
- [AgentLab](https://github.com/ServiceNow/AgentLab)

**Observability and experiment platforms**

- [MLflow GenAI](https://mlflow.org/docs/latest/genai/)
- [Langfuse](https://github.com/langfuse/langfuse)
- [Phoenix](https://github.com/Arize-ai/phoenix)
