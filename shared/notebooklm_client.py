"""
NotebookLM client — knowledge retrieval from Google NotebookLM.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Used by support_bot.py for grounded Q&A.

NotebookLM doesn't expose a public API — this module provides a
graceful stub that returns empty results when the service is
unavailable, preventing import errors in downstream consumers.
"""

import os
from shared.env_loader import load_env_for_source

load_env_for_source()

# Daily query budget (conservative default)
_DAILY_BUDGET = int(os.getenv("NOTEBOOKLM_DAILY_BUDGET", "50"))
_queries_used = 0


def budget_remaining() -> int:
    """Return the estimated remaining query budget for today."""
    return max(0, _DAILY_BUDGET - _queries_used)


def query(question: str, max_chars: int = 3500) -> str:
    """Query NotebookLM for grounded context.

    Since NotebookLM lacks a public REST API, this returns an empty string
    as a graceful fallback. Downstream callers (support_bot.py) treat empty
    context as "no grounded knowledge available" and fall back to LLM-only.

    When a NotebookLM API becomes available, implement the actual call here.
    """
    global _queries_used
    _queries_used += 1
    # Stub — returns empty context
    return ""
