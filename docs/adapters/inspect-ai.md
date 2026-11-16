# Inspect AI adapter

Inspect AI is the workbench's first live runtime integration, not a dependency
of the framework-neutral evaluation core.

[`inspect_adapter.py`](../../src/agent_eval/trace/inspect_adapter.py) converts
successful Inspect sample logs into canonical trajectories. The `agent-eval
run` command executes an Inspect task, normalizes its log, and evaluates the
result. A saved trajectory can later be replayed with `agent-eval evaluate`
without rerunning Inspect or the model.

## Source-specific behavior

- Resolve Inspect attachment placeholders before reading tool arguments and
  results.
- Preserve tool calls, results, errors, and sample metadata.
- Treat the runtime log as the source of execution truth; evaluators operate
  only after normalization.

See [Authoring an adapter](./authoring.md) for the shared contract and
[`src/agent_eval/tasks/README.md`](../../src/agent_eval/tasks/README.md) for
the current Inspect task integration.
