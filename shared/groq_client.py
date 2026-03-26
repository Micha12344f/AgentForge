"""
Groq LLM client via the OpenAI-compatible API.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Same interface as gemini_client and openrouter_client.

Env vars:
    GROQ_API_KEY — Groq API key
"""

import os
import time
from typing import Any, Optional

import requests
from shared.env_loader import load_env_for_source

load_env_for_source()

BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile")


def _api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise RuntimeError("GROQ_API_KEY must be set in .env")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def chat(
    messages: list[dict[str, Any]],
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    response_format: Optional[dict[str, Any]] = None,
    max_retries: int = 3,
    _return_full: bool = False,
) -> str | dict[str, Any]:
    """Send a chat completion request to Groq.

    Matches the same signature as gemini_client.chat and openrouter_client.chat.
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=_headers(),
                json=payload,
                timeout=60,
            )
            if response.status_code == 429:
                retry_after = float(response.headers.get("retry-after", 2 ** attempt))
                time.sleep(retry_after)
                continue
            if response.status_code in (500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            data = response.json()
            if _return_full:
                return data
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            last_error = TimeoutError(f"Groq timeout after 60s (attempt {attempt + 1})")
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
        if attempt < max_retries:
            time.sleep(2 ** attempt)

    raise last_error or RuntimeError("Groq request failed")
