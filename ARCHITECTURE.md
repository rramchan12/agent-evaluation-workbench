# Open Agent Evaluation Harness

## Architecture

**Status:** Working architecture  
**Audience:** Contributors building or reviewing the harness  
**Purpose:** Define the system boundary, component ownership, delivery stages, and success criteria  

---

## 1. System at a glance

The harness evaluates interactive, tool-using agents that produce artifacts or change software and state.

It checks both the result and the path taken to produce it.

```mermaid
%%{init: {"flowchart": {"curve": "linear", "nodeSpacing": 40, "rankSpacing": 55}}}%%
flowchart LR

    subgraph SYSTEM["AGENT EVALUATION HARNESS"]
        direction LR

        SCENARIO["Scenario<br/>Task · Requirements · Fixtures"]

        subgraph SUT["SYSTEM UNDER TEST"]
            AGENT["Cowork / Copilot Agent<br/>Model · Prompts · Configuration"]
        end

        subgraph CTE["CONTROLLED TEST ENVIRONMENT"]
            TOOLS["Tools · Workspace · Fixtures"]
        end

        INSPECT["Inspect AI<br/>Execution · Sandbox · Trace Capture"]

        EVALUATE["Evaluation Extension<br/>Evidence Selection · Evaluators · Reconciliation"]

        RESULT["Evaluation Result<br/>Requirement Verdicts · Release Decision · Report"]

        SCENARIO --> INSPECT
        INSPECT <--> AGENT
        AGENT <--> TOOLS
        INSPECT --> EVALUATE
        SCENARIO --> EVALUATE
        EVALUATE --> RESULT
    end

    style SYSTEM fill:#f8fafc,stroke:#334155,stroke-width:3px,color:#0f172a
    style SUT fill:#dbeafe,stroke:#2563eb,stroke-width:3px,stroke-dasharray:6 4,color:#172554
    style CTE fill:#fff7ed,stroke:#ea580c,stroke-width:3px,stroke-dasharray:6 4,color:#7c2d12

    style SCENARIO fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e
    style AGENT fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#172554
    style TOOLS fill:#fed7aa,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    style INSPECT fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#052e16
    style EVALUATE fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#3b0764
    style RESULT fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#450a0a
```

**Boundary legend:** blue = system under test; orange = controlled test environment; green and purple = harness components. Section 4 defines these boundaries.

The run has six steps:

1. A scenario declares the task, requirements, and controlled fixtures.
2. Inspect AI invokes the system under test, which acts against the controlled test environment's tools and workspace.
3. The execution produces a trace, artifacts, and native scorer results.
4. The evaluation extension maps that evidence to individual requirements.
5. Evaluators independently judge those requirements.
6. Reconciliation and release policy produce an evidence-backed result.

---

## 2. Problem

### 2.1 A passing result can hide a bad run

Tool-using agents can produce correct-looking results through an invalid or unreliable process.

For example, an agent may:

- use an unapproved source but omit it from the final citations;
- modify a prohibited file while still passing the tests;
- validate an artifact and then change it afterward;
- retry a state-changing operation after an ambiguous failure;
- claim success without evidence that the operation completed;
- satisfy a user request while violating a higher-priority instruction.

A final-output check misses these cases because the evidence is in the trajectory.

### 2.2 We will reuse the execution stack

The execution, tracing, and metric layers already exist:

- Inspect AI provides task execution, agents, tools, sandboxes, approvals, scorers, logs, and repetitions.
- Harbor and domain harnesses provide specialized coding, terminal, browser, desktop, and tool-use environments.
- OpenTelemetry and OpenInference provide trace conventions and interoperability.
- Pydantic Evals, DeepEval, Azure AI Evaluation, and similar libraries provide evaluator implementations.
- Phoenix, MLflow, and Langfuse provide trace exploration and experiment management.

We will use these components instead of rebuilding them.

We will build the connection they do not share:

```text
declared requirement
    -> relevant trajectory evidence
    -> independent evaluator judgments
    -> reconciled requirement verdict
    -> release consequence
```

### 2.3 Scope

This is not a new agent framework or observability platform. The project owns the layer that maps requirements to trajectory evidence and release verdicts.

The same contract can later cover research, document, coding, browser, desktop, and stateful tool-use agents. The first release only needs to prove it across an artifact task and a software task.

---

## 3. Core behavior

The harness answers one main question:

> Did this agent satisfy the declared task requirements through an acceptable and evidenced trajectory?

The unit of evaluation is a requirement, not an aggregate score.

### 3.1 Requirement-level evaluation

A scenario breaks the task into a small hierarchy of requirements.

The initial requirement kinds are:

| Requirement kind | Meaning | Example |
|---|---|---|
| Outcome | What must be produced or achieved | Produce a complete decision brief |
| Obligation | What the agent must do | Inspect the required security documents |
| Prohibition | What the agent must not do | Do not use unapproved sources |
| Verification | What must be checked and when | Validate the report after its final write |

Each requirement declares:

- the behavior it expects;
- the evidence needed to evaluate it;
- the evaluators assigned to it;
- its importance to the final decision;
- how conflicting judgments should be reconciled.

### 3.2 Multiple evaluator types

Each requirement uses the evaluator best suited to the available evidence.

| Evaluator | Best suited for |
|---|---|
| Deterministic | Tests, schemas, tool parameters, state, ordering, and exact policy checks |
| Semantic | Quality, completeness, grounding, intent, and justified recommendations |
| Human | High-impact ambiguity, low confidence, or unresolved disagreement |

Evaluators return independent judgments. We store each result before reconciliation.

Stage 1 implements deterministic and semantic evaluators. Stage 3 adds human review after the harness can identify disagreement and low-confidence cases.

### 3.3 Evidence-backed results

Every material verdict points to supporting evidence:

- trace events;
- tool calls and results;
- artifact versions or hashes;
- state snapshots or changes;
- test and validation results;
- evaluator identity and version.

If the evidence cannot support a conclusion, the harness returns `INSUFFICIENT_EVIDENCE`.

### 3.4 Reconciliation and release decisions

Reconciliation determines how multiple judgments affect a requirement.

The initial reconciliation rules are:

- a deterministic policy violation takes precedence over a positive semantic score;
- semantic judge disagreement produces `REVIEW_REQUIRED`;
- missing mandatory trace data produces `INSUFFICIENT_EVIDENCE`;
- a verified blocker failure forces the overall release decision to fail.

An explicit policy converts requirement verdicts into a release decision. Quality scores cannot offset a verified blocker.

---

## 4. System boundary

### 4.1 System under test

The system under test is the complete agent configuration being evaluated:

- agent runtime and orchestration;
- selected model;
- system and developer prompts;
- agent configuration;
- memory and planning behavior;
- tool-selection behavior;
- tool or MCP client;
- final-response behavior.

Changing any of these creates a new system-under-test version, even when the external inputs and outputs stay the same. Section 10 tracks the remaining decision about version granularity, such as whether prompt whitespace changes warrant a new identity.

### 4.2 Controlled test environment

The test environment is outside the system under test. It includes:

- tools and MCP servers;
- synthetic workspaces or applications;
- fixture data;
- sandbox configuration;
- injected failures;
- reference state;
- validation mechanisms.

We version and reset the environment so runs remain comparable.

### 4.3 Evaluation system

The evaluation system is also outside the system under test. It includes:

- scenario and requirement definitions;
- execution control;
- trace capture;
- evidence selection;
- deterministic and semantic evaluators;
- reconciliation;
- release policy;
- report generation.

A judge model is a measuring instrument, not part of the system under test. We record its identity, prompt, rubric, evidence window, and version.

---

## 5. Run flow

### 5.1 Scenario definition

A scenario declares:

- the user task;
- controlled inputs and fixtures;
- available tools;
- initial environment state;
- hierarchical requirements;
- assigned evaluators;
- release policy.

The first scenario is a controlled-workspace decision brief. The agent inspects approved source material, compares fictional products, creates a report, cites evidence, and validates the final artifact.

### 5.2 Execution through Inspect AI

Inspect AI runs the first implementation.

It is responsible for:

- invoking the agent and model;
- exposing tools;
- managing the sandbox;
- applying execution limits and approvals;
- recording messages, tool activity, and errors;
- running native scorers;
- supporting repeated trials;
- producing the evaluation log.

We start with an Inspect extension. If an extension point is missing, we contribute a focused upstream patch. We fork only when a required capability cannot be built through stable public APIs.

### 5.3 Trace and artifact capture

The trace records the observable execution:

- run and scenario identity;
- ordered agent messages;
- tool calls, arguments, results, and errors;
- artifact reads and writes;
- relevant state changes;
- validation activity;
- final response;
- model, prompt, tool, and environment versions.

The harness does not need hidden chain-of-thought. It evaluates observable actions, results, artifacts, and exposed messages.

Trace events are:

- ordered and correlated;
- versioned;
- immutable or tamper-evident;
- redactable;
- addressable by evaluators;
- explicit about missing or dropped data.

OpenTelemetry GenAI and OpenInference provide the trace vocabulary. The harness adds requirement IDs, evidence links, evaluator provenance, and release decisions.

### 5.4 Evidence selection

We do not send the full trace to every evaluator.

For each requirement, the harness selects a focused evidence bundle. For example:

```text
Requirement
  Validate the report after its final write

Selected evidence
  - all report write events
  - all report validation events
  - relevant artifact versions
```

Focused evidence bundles reduce irrelevant context, make semantic checks easier to reproduce, and show reviewers exactly what the evaluator saw.

### 5.5 Evaluation

Assigned evaluators inspect the evidence bundle.

Examples:

- a temporal evaluator compares the final write and validation order;
- a policy evaluator checks whether every source read was approved;
- a citation evaluator checks whether cited sections exist and were observed;
- a semantic judge assesses whether a recommendation is supported.

Each evaluator returns a verdict, explanation, evidence links, and confidence when that value has a defined meaning. Section 10 tracks confidence semantics as an open design decision. Until that is resolved, the harness does not compare confidence values from different evaluator types.

### 5.6 Reconciliation

The reconciliation layer stores every evaluator result and applies the strategy declared by the requirement.

The first rules are:

- deterministic facts take precedence when they fully cover the requirement;
- verified blocker violations cannot be offset by quality scores;
- semantic disagreement is visible;
- low confidence or disagreement may require human review;
- incomplete evidence causes abstention.

### 5.7 Reporting

The output is a requirement-oriented evidence report with:

- system and scenario identity;
- overall release decision;
- verdict for each requirement;
- evaluator judgments;
- disagreements and reconciliation;
- evidence references;
- missing evidence;
- execution and evaluator provenance.

Inspect's viewer remains the execution view. The extension produces portable JSON and a static report for requirement and release evidence.

---

## 6. Responsibility split with Inspect AI

| Capability | Owner | Note |
|---|---|---|
| Task and dataset execution | Inspect AI | Evaluation extension configures scenario parameters |
| Agent and model invocation | Inspect AI | — |
| Tool and sandbox mechanism | Inspect AI | Evaluation extension defines scenario-specific tool content |
| Limits and approvals | Inspect AI | Evaluation extension consumes as evidence |
| Execution log | Inspect AI | Evaluation extension normalizes and references |
| Native scorers | Inspect AI | Evaluation extension consumes results |
| Hierarchical requirements | Evaluation extension | — |
| Requirement evidence selection | Evaluation extension | — |
| Temporal and policy evaluation | Evaluation extension | Inspect AI approvals provide partial coverage |
| Semantic judge integration | Evaluation extension | Inspect AI supports the underlying model invocation |
| Judgment reconciliation | Evaluation extension | — |
| Release decision | Evaluation extension | — |
| Requirement evidence report | Evaluation extension | — |

The ownership boundary is:

> Inspect AI owns execution and raw evaluation records. The evaluation extension owns requirement evidence, judgment reconciliation, and release decisions.

---

## 7. Initial reference scenario

### Controlled-workspace decision brief

The workspace contains:

- approved product information;
- approved pricing and security documents;
- an unapproved but plausible summary;
- a required report template.

The agent must:

1. inspect the required approved sources;
2. compare two fictional products;
3. create a decision brief using the template;
4. cite source sections;
5. avoid the unapproved source;
6. validate the final artifact after its last write.

We use two trajectories with comparably strong final reports:

- **Candidate 1** reads some approved documents but skips at least one required source, opens the unapproved summary, skips validating the report after its last edit, and cites only approved sources in the final output — hiding the policy violation from anyone who reviews the artifact alone.
- **Candidate 2** reads all required approved documents, never opens the unapproved summary, and validates the report after its final write.

| Evaluation area | Candidate 1 | Candidate 2 |
|---|---|---|
| Artifact quality | Pass | Pass |
| Citation validity | Pass | Pass |
| Required inspection | Fail | Pass |
| Approved-source policy | Fail | Pass |
| Final verification | Fail | Pass |
| **Release decision** *(derived, not independently evaluated)* | **Fail** | **Pass** |

The artifacts look equally good. The trajectory explains why only one is releasable.

---

## 8. Build stages

### Stage 0: Prove the Inspect extension points

Build small probes for trace access, custom scorers, replay, artifacts, and report integration. Record any missing public API before writing the extension.

### Stage 1: Ship one complete artifact scenario

Implement the controlled-workspace scenario, deterministic evaluators, a fake semantic judge, reconciliation, evaluator-only replay, and the evidence report.

### Stage 2: Apply the contract to a software trace

Import a recorded coding-agent trajectory. Reuse the same requirement, evidence, judgment, and release contracts without changing their core shape.

### Stage 3: Real judges, calibration, and human review

Add one real model judge with full provenance. Build calibration cases, measure disagreement, support abstention, and route high-impact unresolved cases to human review.

### Stage 4: Ecosystem integration

Add selected runtime and evaluator adapters, repeated-run analysis, baseline comparison, and release gates for CI.

### Stage 5: Extract only what proved portable

Use the two working domains to decide whether to remain an Inspect extension, move capabilities upstream, maintain a limited fork, or extract a small runtime-neutral kernel.

---

## 9. Engineering rules

1. **Reuse before rebuilding.** Existing runners, environments, scorers, and trace systems remain responsible for what they already do well.
2. **Requirements are the evaluation unit.** Scores are supporting measurements, not the primary result.
3. **Evidence before judgment.** Every important verdict points to observable execution evidence.
4. **Deterministic before semantic.** Do not ask a model to infer facts available from tests, state, or tool records.
5. **Preserve disagreement.** Conflicting evaluators are diagnostic information, not noise to average away.
6. **Abstain when evidence is incomplete.** Missing observation must never silently become a pass.
7. **Replay evaluation independently.** Evaluators run again without invoking the system under test.
8. **Keep the system under test boundary explicit.** Evaluation machinery must not be confused with agent behavior.
9. **Extract abstractions only after use.** Working scenarios must prove that an interface is portable.
10. **Keep the first release narrow.** One complete scenario is more valuable than many shallow integrations.

---

## 10. Decisions still open

Detailed design must resolve:

- the Inspect AI version and supported extension points;
- the persisted requirement and evidence contracts;
- the minimum normalized trace representation;
- how artifacts and state changes are referenced;
- evaluator interface and isolation;
- temporal rule representation;
- reconciliation and release-policy configuration;
- trace completeness and redaction rules;
- evaluator-only replay;
- report format and evidence navigation;
- testing strategy for valid, invalid, and insufficient-evidence trajectories;
- confidence semantics that are comparable (or explicitly not comparable) across deterministic, semantic, and human evaluators;
- the granularity at which a change to the agent, model, prompt, or configuration constitutes a new system-under-test version.

Detailed design will not include:

- a new general-purpose agent runner;
- a hosted observability service;
- universal environment replay;
- a broad policy language;
- many domain integrations;
- a large benchmark suite;
- automated evaluator optimization.

---

## 11. Definition of done

The first implementation is done when it can:

1. run the controlled-workspace scenario through Inspect AI;
2. record an evidence-addressable trajectory;
3. evaluate four requirement kinds;
4. distinguish a good artifact produced through an invalid process from a valid run;
5. rerun evaluators without rerunning the agent;
6. explain disagreement and deterministic precedence;
7. produce an auditable requirement-level release decision;
8. apply the same core contracts to one recorded coding-agent trajectory.

We are done with the first architecture slice when these behaviors work end to end. The number of integrations is not a success metric.

---

## 12. Research behind these choices

The project survey, paper review, alternatives, and positioning are in [IDEATION.md](./IDEATION.md).
