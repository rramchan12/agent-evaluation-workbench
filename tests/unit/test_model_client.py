"""Unit tests for the stdlib judge model client."""

from __future__ import annotations

import pytest

from agent_eval.evaluators.semantic.model_client import ScriptedModelClient, get_model_client


def test_scripted_client_repeats_last_response():
    client = ScriptedModelClient(["a", "b"])
    assert [client.generate("s", "p") for _ in range(3)] == ["a", "b", "b"]


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError, match="unsupported judge model"):
        get_model_client("anthropic/claude")


def test_openai_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_model_client("openai/gpt-4o-mini")
