"""agent_eval: a replay-capable evaluation harness for tool-using agents.

The harness never runs an agent and has no agent-framework dependency. Agents
run elsewhere; their traces reach this package only through adapters in
``trace`` that produce a normalized ``Trajectory``, which is all ``core`` and
``evaluators`` consume.
"""

__version__ = "0.1.0"
