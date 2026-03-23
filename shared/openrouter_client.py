"""
OpenRouter chat client using the OpenAI-compatible API.
"""

import os
import time
from typing import Any, Optional

import requests
from shared.env_loader import load_env_for_source


def _load_env() -> None:
    load_env_for_source()


_load_env()

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-flash")


def _api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY") or ""
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY must be set in .env")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", "https://hedgedge.info"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "Hedge Edge Orchestrator"),
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
                time.sleep(float(response.headers.get("retry-after", 2 ** attempt)))
                continue
            if response.status_code in (500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            data = response.json()
            if _return_full:
                return data
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout as exc:
            last_error = TimeoutError(f"OpenRouter timeout after 60s (attempt {attempt + 1})")
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
        if attempt < max_retries:
            time.sleep(2 ** attempt)

    raise last_error or RuntimeError("OpenRouter request failed")