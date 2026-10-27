import pytest

from app.infrastructure.llm_client import LiteLLMConfigurationError, LiteLLMSettings


def test_settings_read_gateway_environment(monkeypatch):
    monkeypatch.setenv("LITELLM_API_BASE", "https://gateway.example/v1/")
    monkeypatch.setenv("LITELLM_API_KEY", "test-key")
    monkeypatch.setenv("LITELLM_MODEL", "azure_ai/claude-haiku-5-5")

    settings = LiteLLMSettings.from_environment()

    assert settings.api_base == "https://gateway.example/v1"
    assert settings.api_key == "test-key"
    assert settings.model == "azure_ai/claude-haiku-5-5"


def test_settings_fail_when_gateway_key_is_missing(monkeypatch):
    monkeypatch.setenv("LITELLM_API_BASE", "https://gateway.example/v1")
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)

    with pytest.raises(LiteLLMConfigurationError, match="LITELLM_API_KEY"):
        LiteLLMSettings.from_environment()


def test_complete_routes_through_the_openai_compatible_gateway(monkeypatch):
    from app.infrastructure import llm_client

    calls = {}
    monkeypatch.setattr(llm_client.litellm, "completion", lambda **kwargs: calls.update(kwargs))
    settings = LiteLLMSettings("https://gateway.example/v1", "test-key", "azure_ai/claude-haiku-5-5")

    llm_client.complete([{"role": "user", "content": "hi"}], settings=settings)

    assert calls["model"] == "openai/azure_ai/claude-haiku-5-5"
    assert calls["api_base"] == "https://gateway.example/v1"
