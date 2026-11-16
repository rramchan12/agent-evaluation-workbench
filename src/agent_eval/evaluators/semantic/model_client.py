"""Minimal, dependency-free model client used by the real judge.

A judge model is a measuring instrument, so all it needs is
``generate(system_prompt, prompt) -> str``. Two implementations:

- ``ScriptedModelClient``: returns canned responses (tests, calibration, and
  the free default -- no network, no key).
- ``OpenAICompatibleClient``: POSTs to any OpenAI-compatible
  ``/chat/completions`` endpoint using only the standard library.

Model names are ``<provider>/<model>``. ``mock/...`` selects the scripted
client; ``openai/<model>`` the HTTP client (``OPENAI_API_KEY``, optional
``OPENAI_BASE_URL``).
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Iterable, Protocol

DEFAULT_MODEL = "mock/model"
DEFAULT_MOCK_RESPONSE = "Default output from mock/model"


class ModelClient(Protocol):
    def generate(self, system_prompt: str, prompt: str) -> str: ...


class ScriptedModelClient:
    """Yields scripted responses in order; repeats the last one when exhausted."""

    def __init__(self, responses: Iterable[str] | None = None) -> None:
        self._responses = list(responses) if responses is not None else [DEFAULT_MOCK_RESPONSE]
        self._index = 0

    def generate(self, system_prompt: str, prompt: str) -> str:
        if not self._responses:
            return DEFAULT_MOCK_RESPONSE
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return response


class OpenAICompatibleClient:
    def __init__(self, model: str, api_key: str, base_url: str, timeout: float = 60.0) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, system_prompt: str, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"] or ""


def get_model_client(name: str, mock_responses: list[str] | None = None) -> ModelClient:
    """Build a client from ``mock_responses`` (wins) or a ``provider/model`` name."""
    if mock_responses is not None:
        return ScriptedModelClient(mock_responses)
    provider, _, model = name.partition("/")
    if provider == "mock":
        return ScriptedModelClient()
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set to use an 'openai/...' judge model")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAICompatibleClient(model, api_key, base_url)
    raise ValueError(
        f"unsupported judge model '{name}': expected 'mock/...' or 'openai/<model>'"
    )
