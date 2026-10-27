"""Small client for the project's OpenAI-compatible LiteLLM gateway."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import litellm



class LiteLLMConfigurationError(RuntimeError):
    """Raised when required LiteLLM connection settings are missing."""


@dataclass(frozen=True)
class LiteLLMSettings:
    api_base: str
    api_key: str
    model: str

    @classmethod
    def from_environment(cls) -> "LiteLLMSettings":
        values = {
            "api_base": os.getenv("LITELLM_API_BASE", "").rstrip("/"),
            "api_key": os.getenv("LITELLM_API_KEY", ""),
            "model": os.getenv("LITELLM_MODEL", "azure_ai/claude-haiku-5-5"),
        }
        missing = [name for name in ("api_base", "api_key") if not values[name]]
        if missing:
            names = ", ".join(f"LITELLM_{name.upper()}" for name in missing)
            raise LiteLLMConfigurationError(f"Missing required environment variable(s): {names}")
        return cls(**values)


def complete(
    messages: list[dict[str, str]],
    *,
    settings: LiteLLMSettings | None = None,
    **kwargs: Any,
) -> Any:
    """Send a chat completion through the configured LiteLLM gateway."""

    connection = settings or LiteLLMSettings.from_environment()
    return litellm.completion(
        model=f"openai/{connection.model}",
        messages=messages,
        api_base=connection.api_base,
        api_key=connection.api_key,
        **kwargs,
    )
