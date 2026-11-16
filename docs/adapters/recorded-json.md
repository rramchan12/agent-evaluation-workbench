# Recorded JSON adapter

The recorded JSON adapter imports a flat, ordered step list without loading an
agent runtime. It is the simplest interchange format for hand-authored fixtures,
external capture scripts, and evaluator-only replay.

[`import_recorded.py`](../../src/agent_eval/trace/import_recorded.py) accepts:

```json
{
  "trajectory_id": "run-1",
  "scenario_id": "example",
  "system_under_test": "recorded-agent",
  "complete": true,
  "final_output": "Done",
  "artifacts": {},
  "steps": [
    {
      "kind": "tool_call",
      "name": "read_file",
      "arguments": {"path": "README.md"},
      "result": "..."
    }
  ]
}
```

The importer assigns canonical event IDs in list order. Use `complete=false`
and `incompleteness_reason` when the recording is partial.

Run it through the harness with:

```powershell
agent-eval evaluate `
  --scenario scenarios/coding-agent-bugfix/scenario.json `
  --trajectory traces/coding-bugfix-good.json `
  --out-dir out
```

See [Authoring an adapter](./authoring.md) before generating recorded JSON from
another runtime. A source-specific adapter is preferable when flattening would
discard important provenance or completeness information.
