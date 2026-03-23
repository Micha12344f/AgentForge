"""
Hedge Edge — Support Bot
========================
Grounded support bot that combines NotebookLM knowledge retrieval
with Groq llama-3.3-70b for high-quality Discord support responses.

Used by interactions_server.py when agent_key == "community-manager".

Flow:
  1. Query NotebookLM "Hedge Edge Support" notebook for grounded context
  2. Feed context + specialized system prompt to Groq
  3. Return a concise, accurate, cited answer
"""

import os
import logging
from shared.notebooklm_client import query as nlm_query, budget_remaining
from shared.groq_client import chat

_log = logging.getLogger("support_bot")

MODEL = os.environ.get("SUPPORT_BOT_MODEL", "llama-3.3-70b-versatile")

# ── System prompt ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are the Hedge Edge Support Bot — a helpful, knowledgeable assistant embedded \
in the Hedge Edge Discord community.

YOUR MISSION: Answer user questions about Hedge Edge accurately, using ONLY the \
grounded knowledge provided in the CONTEXT section below. If the context doesn't \
cover the question, say "I don't have specific information about that — please \
post in #hedge-setup-help and someone from the team will help you."

PERSONA:
- Friendly but professional. You're a product expert, not a chatbot.
- Use clear, step-by-step instructions for setup/technical questions.
- For prop firm rule questions, ALWAYS add: "Rules can change — verify directly \
with your prop firm before relying on this."
- Never promise features that aren't confirmed as live.
- Never generate code or scripts.

WHAT YOU KNOW (from your knowledge base):
- How prop firm hedging works (capital preservation strategy)
- EA installation and setup (MT5, planned MT4/cTrader)
- Broker setup (Vantage, BlackBull)
- Subscription tiers (Free Hedge Guide, Challenge Shield $29/mo, Multi-Challenge, Unlimited)
- Common issues and troubleshooting (EA connection, broker linking, hedge execution)
- Onboarding flow (download → install EA → link broker → first hedge)

FORMAT RULES:
- Keep answers under 1800 characters (Discord embed limit).
- Use Markdown: **bold** for emphasis, bullet points for steps.
- For multi-step instructions, use numbered lists.
- If the answer involves an external link, mention it but clarify you can't \
generate actual URLs."""


def answer(
    question: str,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generate a grounded support response.

    Args:
        question:              The user's support question.
        conversation_history:  Prior conversation turns [{role, content}, ...].

    Returns:
        The support bot's answer text.
    """
    # 1 — Retrieve grounded context from NotebookLM
    context = ""
    remaining = budget_remaining()
    if remaining > 0:
        context = nlm_query(question, max_chars=3500)
        if context:
            _log.info(
                f"[SupportBot] NotebookLM: {len(context)} chars "
                f"({remaining - 1} queries left today)"
            )

    # 2 — Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history[-6:])  # last 3 turns

    if context:
        user_content = (
            f"GROUNDED KNOWLEDGE (from Hedge Edge documentation):\n---\n"
            f"{context}\n---\n\n"
            f"Answer using ONLY the information above. "
            f"If it doesn't address their question, say so honestly.\n\n"
            f"USER QUESTION: {question}"
        )
    else:
        user_content = (
            "No grounded context available for this question. "
            "Answer from your general knowledge about Hedge Edge if possible, "
            "otherwise direct the user to #hedge-setup-help.\n\n"
            f"USER QUESTION: {question}"
        )

    messages.append({"role": "user", "content": user_content})

    # 3 — Generate via Groq
    _log.info(f"[SupportBot] Generating with {MODEL}")
    return chat(
        messages=messages,
        model=MODEL,
        temperature=0.3,
        max_tokens=1024,
    )
