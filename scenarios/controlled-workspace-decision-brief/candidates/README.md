# candidates/

Hand-authored tool-call trajectories (`steps[]` + `final_message`) that a
scripted mockllm replays through `src/agent_eval/tasks/decision_brief.py`,
so the `controlled-workspace-decision-brief` scenario runs deterministically
under live Inspect AI without a real model.

Each `candidate-N.json` represents a different behavior worth testing
against the scenario's requirements (e.g. skipping an approved source,
reading an unapproved document, validating before rather than after the
final write). The expected verdict for each candidate lives under
`../expected/candidate-N.json`.
