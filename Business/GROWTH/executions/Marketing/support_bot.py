#!/usr/bin/env python3
"""
Hedge Edge — Community Manager Support Bot
===========================================
NotebookLM-grounded support bot for Discord.

Flow:
  1. User asks question via Discord /ask (routed to community-manager)
  2. NotebookLM retrieves grounded context from "Hedge Edge Support" notebook
  3. Groq llama-3.3-70b synthesises a helpful answer using that context
  4. Response posted back to Discord with sources

The notebook contains (customer-safe only — no internal architecture):
  - EA Installation Guide (step-by-step MT5 setup + troubleshooting)
  - Product FAQ (pricing, brokers, accounts, common questions)
  - Hedging Explained (beginner guide to prop firm hedging)
  - How to Hedge Prop Firms (PDF guide)

Usage:
    from support_bot import answer
    response = answer("How do I install the EA on MT5?")
"""

import os
import sys
import logging

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(15):
        if os.path.isfile(os.path.join(d, "shared", "notion_client.py")) and os.path.isdir(os.path.join(d, "Business")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Cannot locate workspace root")

_WS_ROOT = _find_ws_root()
if _WS_ROOT not in sys.path:
    sys.path.insert(0, _WS_ROOT)

from shared.notebooklm_client import query as nlm_query, budget_remaining
from shared.groq_client import chat

_log = logging.getLogger("support_bot")

# ── Model ────────────────────────────────────────────────────────────────
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
- If the answer involves an external link (broker signup, prop firm rules), mention \
it but clarify you can't generate actual URLs.
"""

CONTEXT_TEMPLATE = """\
GROUNDED KNOWLEDGE (from Hedge Edge documentation):
---
{context}
---

Answer the user's question using ONLY the information above. If the context \
doesn't address their question, say so honestly."""


def answer(
    question: str,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generate a grounded support response.

    1. Queries NotebookLM for relevant context
    2. Feeds context + question to Groq LLM
    3. Returns the answer

    Args:
        question:              The user's support question.
        conversation_history:  Prior conversation turns (for multi-turn context).

    Returns:
        The support bot's response text.
    """
    # Step 1: Retrieve grounded knowledge from NotebookLM
    context = ""
    remaining = budget_remaining()
    if remaining > 0:
        context = nlm_query(question, max_chars=3500)
        if context:
            _log.info(f"[SupportBot] NotebookLM returned {len(context)} chars "
                      f"({remaining - 1} queries remaining today)")

    # Step 2: Build messages for Groq
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history[-6:])

    if context:
        user_content = (
            CONTEXT_TEMPLATE.format(context=context)
            + f"\n\nUSER QUESTION: {question}"
        )
    else:
        user_content = (
            "No grounded context available for this question. "
            "Answer from your general knowledge about Hedge Edge if possible, "
            "otherwise direct the user to #hedge-setup-help.\n\n"
            f"USER QUESTION: {question}"
        )

    messages.append({"role": "user", "content": user_content})

    # Step 3: Generate response via Groq
    _log.info(f"[SupportBot] Generating response with {MODEL}")
    response = chat(
        messages=messages,
        model=MODEL,
        temperature=0.3,
        max_tokens=1024,
    )

    return response


# ── CLI for testing ──────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_WS_ROOT, ".env"))

    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    else:
        q = "How do I install the Hedge Edge EA on MT5?"

    print(f"\nQuestion: {q}")
    print(f"Budget remaining: {budget_remaining()}/5000\n")
    print("=" * 60)
    resp = answer(q)
    print(resp)
    print("=" * 60)
    print(f"\nBudget remaining: {budget_remaining()}/5000")
