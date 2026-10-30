"""The Streamlit evaluation GUI: a presentation layer over ``core.engine``.

Nothing in ``agent_eval.core``, ``agent_eval.evaluators``, or
``agent_eval.trace`` changes for this package to exist — the GUI is a second
caller of ``core.engine.evaluate``, exactly like ``cli.py``. See
``gui/README.md`` for the module breakdown.
"""
