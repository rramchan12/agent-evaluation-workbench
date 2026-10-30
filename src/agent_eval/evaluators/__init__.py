"""Importing this package registers every built-in evaluator (by id) with
``agent_eval.core.evaluators``. Anything that calls ``core.engine.evaluate``
should import ``agent_eval.evaluators`` first (or import it transitively,
as ``cli.py`` and the test fixtures do).
"""

from agent_eval.evaluators.deterministic import checks as _checks  # noqa: F401
from agent_eval.evaluators.semantic import fake_judge as _fake_judge  # noqa: F401
