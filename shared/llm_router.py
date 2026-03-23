"""
Provider-aware LLM routing with agent-specific defaults.
"""

import os
from copy import deepcopy
from typing import Any

from shared.gemini_client import chat as gemini_chat
from shared.groq_client import chat as groq_chat
from shared.openrouter_client import chat as openrouter_chat

_DEFAULT_ANALYTICS_MODEL = os.getenv("ANALYTICS_LLM_MODEL", "gemini-2.5-flash")
_DEFAULT_ANALYTICS_FALLBACK = os.getenv(
    "ANALYTICS_LLM_FALLBACK_MODEL",
    "google/gemini-2.5-flash",
)

AGENT_MODEL_REGISTRY: dict[str, dict[str, dict[str, str] | str]] = {
    "default": {
        "provider": "groq",
        "model": os.getenv("DEFAULT_LLM_MODEL", "llama-3.3-70b-versatile"),
    },
    "analytics": {
        "provider": "gemini",
        "model": _DEFAULT_ANALYTICS_MODEL,
        "fallback_provider": os.getenv("ANALYTICS_LLM_FALLBACK_PROVIDER", "openrouter"),
        "fallback_model": _DEFAULT_ANALYTICS_FALLBACK,
    },
}


def get_agent_model_config(agent_key: str) -> dict[str, str]:
    config = AGENT_MODEL_REGISTRY.get(agent_key, AGENT_MODEL_REGISTRY["default"])
    return deepcopy(config)


def _call_provider(provider: str, messages: list[dict[str, Any]], **kwargs: Any) -> str | dict[str, Any]:
    if provider == "gemini":
        return gemini_chat(messages, **kwargs)
    if provider == "openrouter":
        return openrouter_chat(messages, **kwargs)
    if provider == "groq":
        return groq_chat(messages, **kwargs)
    raise ValueError(f"Unsupported LLM provider: {provider}")


def chat(
    agent_key: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    response_format: dict[str, Any] | None = None,
    _return_full: bool = False,
) -> str | dict[str, Any]:
    config = get_agent_model_config(agent_key)
    primary_kwargs = {
        "model": config["model"],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": response_format,
        "_return_full": _return_full,
    }
    try:
        return _call_provider(config["provider"], messages, **primary_kwargs)
    except Exception:
        fallback_provider = config.get("fallback_provider")
        fallback_model = config.get("fallback_model")
        if not fallback_provider or not fallback_model:
            raise
        fallback_kwargs = {
            "model": fallback_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": response_format,
            "_return_full": _return_full,
        }
        return _call_provider(fallback_provider, messages, **fallback_kwargs)