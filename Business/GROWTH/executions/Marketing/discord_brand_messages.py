"""
Send a branded intro/pinned message to every text channel in the Hedge Edge Discord.
Each message is a rich embed with the channel's purpose, guidelines, and Hedge Edge branding.
Messages are automatically pinned after sending.
"""
import os
import sys
import time
import requests

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, 'shared')) and os.path.isdir(os.path.join(d, 'Business')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

sys.path.insert(0, _find_ws_root())

from dotenv import load_dotenv
load_dotenv(os.path.join(_find_ws_root(), '.env'))

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
API = "https://discord.com/api/v10"

# Brand constants
BRAND_GREEN = 0x00C853
BRAND_RED = 0xFF1744
BRAND_GOLD = 0xFFD700
BRAND_BLUE = 0x2196F3
BRAND_DARK = 0x1A1A2E
BRAND_TEAL = 0x009688
BRAND_PURPLE = 0x9C27B0

FOOTER = {
    "text": "Hedge Edge — Protect Your Challenges, Recover Your Fees",
    "icon_url": "https://cdn.discordapp.com/icons/1101229154386579468/a_placeholder.png"
}

# ─── Fetch emoji IDs ──────────────────────────────────────────────

emojis_raw = requests.get(f"{API}/guilds/{GUILD_ID}/emojis", headers=HEADERS, timeout=10).json()
E = {}
for em in emojis_raw:
    E[em["name"]] = f"<:{em['name']}:{em['id']}>"
print(f"Loaded {len(E)} custom emojis")

# ─── Fetch channels ──────────────────────────────────────────────

channels_raw = requests.get(f"{API}/guilds/{GUILD_ID}/channels", headers=HEADERS, timeout=10).json()
by_name = {}
for ch in channels_raw:
    # strip emoji prefix for matching — use the part after ・ if present
    name = ch.get("name", "")
    clean = name.split("・")[-1] if "・" in name else name
    by_name[clean] = ch
print(f"Loaded {len(channels_raw)} channels\n")

# ─── Helper ───────────────────────────────────────────────────────

def send_embed(channel_name, embed, content=None):
    """Send an embed to a channel and pin it."""
    ch = by_name.get(channel_name)
    if not ch:
        print(f"  ⚠️  '{channel_name}' not found, skipping")
        return False

    ch_id = ch["id"]
    payload = {"embeds": [embed]}
    if content:
        payload["content"] = content

    for attempt in range(4):
        r = requests.post(f"{API}/channels/{ch_id}/messages", headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 429:
            wait = r.json().get("retry_after", 5)
            print(f"    ⏳ Rate limited, waiting {wait}s...")
            time.sleep(wait + 0.5)
            continue
        if r.status_code in (200, 201):
            msg_id = r.json().get("id")
            # Pin the message
            time.sleep(0.5)
            pin_r = requests.put(f"{API}/channels/{ch_id}/pins/{msg_id}", headers=HEADERS, timeout=10)
            pinned = "📌" if pin_r.status_code == 204 else "⚠️pin"
            print(f"  ✅ {pinned} #{channel_name}")
            return True
        else:
            err = r.json().get("message", r.text)
            print(f"  ❌ #{channel_name} — {err}")
            return False

    return False


def e(name):
    """Get custom emoji string, fallback to name if not found."""
    return E.get(name, f":{name}:")

# ─── Channel Messages ────────────────────────────────────────────

MESSAGES = {

    # ━━━ WELCOME ━━━

    "welcome": {
        "title": f"{e('he_hedge')}  Welcome to Hedge Edge",
        "description": (
            f"**The #1 community for prop firm traders who hedge smart.**\n\n"
            f"{e('he_shield')} **What is Hedge Edge?**\n"
            f"We built the tool that protects your prop firm challenges and recovers your fees when things go wrong. "
            f"Think of it as insurance for your trading career.\n\n"
            f"{e('he_verified')} **How it works:**\n"
            f"```\n"
            f"You trade your challenge normally\n"
            f"↓\n"
            f"Hedge Edge mirrors a protective hedge\n"
            f"↓\n"
            f"If you fail → the hedge recovers your fee\n"
            f"If you pass → you keep your funded account\n"
            f"```\n\n"
            f"{e('he_rocket')} **Get Started:**\n"
            f"1️⃣ Read the rules in **#📜・rules**\n"
            f"2️⃣ Grab your roles in **#🎭・roles**\n"
            f"3️⃣ Introduce yourself in **#👤・introductions**\n"
            f"4️⃣ Join the conversation in **#💬・general-chat**\n\n"
            f"Welcome aboard — let's make sure you never lose a challenge fee again. {e('he_bull')}"
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "Hedge Edge — Protect Your Challenges, Recover Your Fees"},
    },

    "rules": {
        "title": f"📜  Server Rules",
        "description": (
            f"By being in this server, you agree to follow these rules. Violations result in warnings, timeouts, or bans.\n\n"
            f"**1. {e('he_verified')} Be Respectful**\n"
            f"No harassment, hate speech, discrimination, or personal attacks. We're all here to grow.\n\n"
            f"**2. {e('he_alert')} No Financial Advice**\n"
            f"Nothing shared here is financial advice. All trading carries risk. Do your own due diligence.\n\n"
            f"**3. {e('he_shield')} No Spam or Self-Promotion**\n"
            f"No unsolicited DMs, affiliate links, or promoting other services without permission.\n\n"
            f"**4. {e('he_lock')} Keep It Legal**\n"
            f"No discussion of account passing services, identity fraud, or any activity that violates prop firm rules.\n\n"
            f"**5. {e('he_target')} Stay On Topic**\n"
            f"Use the right channel for your message. Off-topic posts may be moved or deleted.\n\n"
            f"**6. {e('he_eyes')} No NSFW Content**\n"
            f"Keep everything safe for work. This is a professional trading community.\n\n"
            f"**7. {e('he_crown')} Respect the Staff**\n"
            f"Moderator decisions are final. If you disagree, DM a mod privately — don't argue in public channels.\n\n"
            f"*Breaking these rules will result in:*\n"
            f"`1st offense` → Warning\n"
            f"`2nd offense` → 24h timeout\n"
            f"`3rd offense` → Permanent ban"
        ),
        "color": BRAND_RED,
        "footer": {"text": "Rules last updated — February 2026"},
    },

    "announcements": {
        "title": f"📢  Official Announcements",
        "description": (
            f"This is where we drop all official Hedge Edge news.\n\n"
            f"{e('he_rocket')} **Product updates & new features**\n"
            f"{e('he_fire')} **Partnership announcements**\n"
            f"{e('he_star')} **Community milestones**\n"
            f"{e('he_shield')} **Policy changes & important notices**\n\n"
            f"Turn on notifications for this channel so you never miss an update.\n"
            f"*🔔 Right-click this channel → Notification Settings → All Messages*"
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "Hedge Edge — Official Announcements"},
    },

    "roles": {
        "title": f"🎭  Grab Your Roles",
        "description": (
            f"React to this message to assign yourself roles and unlock channels!\n\n"
            f"{e('he_bull')} — **Prop Firm Trader** — You're actively trading prop firm challenges\n"
            f"{e('he_shield')} — **Hedger** — You use or are interested in Hedge Edge\n"
            f"{e('he_chartup')} — **Forex Trader** — You trade currencies\n"
            f"{e('he_diamond')} — **Crypto Trader** — You trade digital assets\n"
            f"{e('he_fire')} — **Futures Trader** — You trade futures/indices\n"
            f"{e('he_eyes')} — **Lurker** — Just here to learn and observe\n"
            f"{e('he_star')} — **Content Creator** — You make trading content\n\n"
            f"*More roles coming soon — including Beta Tester access!*"
        ),
        "color": BRAND_GOLD,
        "footer": {"text": "React below to get your roles"},
    },

    "introductions": {
        "title": f"👤  Introduce Yourself!",
        "description": (
            f"We'd love to know who you are! Drop a quick intro using this template:\n\n"
            f"```\n"
            f"🏷️ Name / Alias:\n"
            f"📍 Where you're from:\n"
            f"📊 What you trade (forex, indices, crypto, etc.):\n"
            f"🏦 Prop firms you're with:\n"
            f"🛡️ Do you hedge? (yes / no / curious):\n"
            f"🎯 Trading goal for 2026:\n"
            f"```\n\n"
            f"Don't be shy — everyone started somewhere. Welcome to the community! {e('he_welcome')}"
        ),
        "color": BRAND_TEAL,
        "footer": {"text": "Every funded trader was once a beginner"},
    },

    # ━━━ COMMUNITY ━━━

    "general-chat": {
        "title": f"💬  General Chat",
        "description": (
            f"The main hangout for the Hedge Edge community.\n\n"
            f"Talk about anything — markets, strategies, prop firm drama, life wins, "
            f"or just hang out with fellow traders.\n\n"
            f"{e('he_verified')} **Guidelines:**\n"
            f"• Keep it friendly and respectful\n"
            f"• No spam or excessive self-promotion\n"
            f"• Use specific channels for trade ideas, setups, or support\n"
            f"• Have fun — this is your community {e('he_fire')}"
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "Hedge Edge Community"},
    },

    "memes": {
        "title": f"😂  Memes & Fun",
        "description": (
            f"The lighter side of trading. We all need a laugh between candles.\n\n"
            f"{e('he_bear')} *\"I'll just hold through the news...\"*\n"
            f"{e('he_fire')} *margin call speedrun any%*\n"
            f"{e('he_100')} *\"Trust the process\" — guy who just blew his 5th challenge*\n\n"
            f"**Rules:**\n"
            f"• Trading-related memes preferred\n"
            f"• No NSFW content\n"
            f"• No memes targeting specific community members\n"
            f"• Quality > quantity"
        ),
        "color": BRAND_GOLD,
        "footer": {"text": "If you can't laugh at a blown account, are you even a trader?"},
    },

    "wins": {
        "title": f"{e('he_crown')}  Wins & Milestones",
        "description": (
            f"**This is the trophy room.** {e('he_100')}\n\n"
            f"Post your:\n"
            f"{e('he_verified')} Challenge passes\n"
            f"{e('he_profit')} Payout screenshots\n"
            f"{e('he_chartup')} Account milestones\n"
            f"{e('he_star')} Personal trading records\n"
            f"{e('he_target')} Goals achieved\n\n"
            f"Every win matters — from your first green day to your first $10K payout. "
            f"Share it and inspire the community.\n\n"
            f"*Pro tip: Include what strategy/approach helped you win — help others learn from your success.*"
        ),
        "color": BRAND_GOLD,
        "footer": {"text": "Your wins fuel the community"},
    },

    "suggestions": {
        "title": f"💡  Suggestions",
        "description": (
            f"Got an idea to make Hedge Edge or this community better? **We're listening.**\n\n"
            f"**What to post here:**\n"
            f"{e('he_rocket')} Product feature ideas\n"
            f"{e('he_star')} Server improvement suggestions\n"
            f"{e('he_target')} Event or content ideas\n"
            f"{e('he_welcome')} Partnership suggestions\n\n"
            f"**Format your suggestion like this:**\n"
            f"```\n"
            f"💡 Suggestion: [Your idea]\n"
            f"📝 Details: [Why this would help]\n"
            f"👥 Who benefits: [Which users]\n"
            f"```\n\n"
            f"React with 👍 or 👎 on others' suggestions to help us prioritize."
        ),
        "color": BRAND_BLUE,
        "footer": {"text": "Your ideas shape the product roadmap"},
    },

    # ━━━ TRADING ━━━

    "market-talk": {
        "title": f"📊  Market Discussion",
        "description": (
            f"Daily market talk for serious traders.\n\n"
            f"{e('he_bull')} **What to discuss:**\n"
            f"• Forex pairs, indices, gold, oil, crypto\n"
            f"• Key economic events and news impact\n"
            f"• Session-specific analysis (London, NY, Tokyo)\n"
            f"• Institutional order flow and sentiment\n\n"
            f"{e('he_alert')} **Remember:**\n"
            f"• Nothing here is financial advice\n"
            f"• Back up opinions with analysis\n"
            f"• Respect differing viewpoints\n"
            f"• No \"to the moon\" spam — substance over hype"
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "Trade what you see, not what you think"},
    },

    "trade-ideas": {
        "title": f"🎯  Trade Ideas",
        "description": (
            f"Share your setups and analysis with the community.\n\n"
            f"**Post format:**\n"
            f"```\n"
            f"📊 Pair/Asset:\n"
            f"📐 Direction: Long / Short\n"
            f"🎯 Entry:\n"
            f"🛑 Stop Loss:\n"
            f"✅ Take Profit:\n"
            f"📝 Reasoning:\n"
            f"📸 Chart: [attach screenshot]\n"
            f"```\n\n"
            f"{e('he_shield')} **Guidelines:**\n"
            f"• Include your reasoning — not just levels\n"
            f"• Attach chart screenshots when possible\n"
            f"• Update if your bias changes\n"
            f"• This is NOT financial advice — trade at your own risk"
        ),
        "color": BRAND_BLUE,
        "footer": {"text": "Share the setup, not the signal"},
    },

    "trade-journal": {
        "title": f"📓  Trade Journal",
        "description": (
            f"**The most underrated edge in trading: journaling.** {e('he_diamond')}\n\n"
            f"Create a thread to track your journey. Include:\n"
            f"• Daily/weekly P&L\n"
            f"• Trade screenshots with annotations\n"
            f"• What worked vs. what didn't\n"
            f"• Emotional state and mindset notes\n"
            f"• Rule violations and lessons learned\n\n"
            f"{e('he_chartup')} Traders who journal consistently improve 2-3x faster.\n\n"
            f"*Start a new thread with your name/alias as the title.*"
        ),
        "color": BRAND_TEAL,
        "footer": {"text": "Document the process, not just the results"},
    },

    "strategies": {
        "title": f"🧠  Strategies",
        "description": (
            f"The strategy lab. Share, discuss, and refine your trading edge.\n\n"
            f"{e('he_target')} **Topics for this channel:**\n"
            f"• Trading strategies and methodologies\n"
            f"• Backtesting results and statistics\n"
            f"• ICT, SMC, price action, indicator-based — all welcome\n"
            f"• Strategy optimization and adaptation\n"
            f"• Edge development and market structure\n\n"
            f"{e('he_eyes')} **Best practices:**\n"
            f"• Share results with data, not just theory\n"
            f"• Be specific — \"buy low sell high\" isn't a strategy\n"
            f"• Constructive criticism only\n"
            f"• Give credit where it's due"
        ),
        "color": BRAND_PURPLE,
        "footer": {"text": "An edge is only an edge if you can define it"},
    },

    "risk-management": {
        "title": f"{e('he_shield')}  Risk Management",
        "description": (
            f"**The single most important channel in this server.**\n\n"
            f"If you can't manage risk, nothing else matters.\n\n"
            f"{e('he_alert')} **Core Topics:**\n"
            f"• Position sizing and lot calculations\n"
            f"• Daily drawdown limits (prop firm rules)\n"
            f"• Max loss per trade / per day / per week\n"
            f"• Correlation risk between trades\n"
            f"• Recovery strategies after drawdown\n\n"
            f"{e('he_verified')} **The Hedge Edge Rule of Thumb:**\n"
            f"```\n"
            f"Risk per trade:  0.5% - 1% of account\n"
            f"Max daily loss:  2% - 3% of account\n"
            f"Max open risk:   3% - 5% of account\n"
            f"Correlation cap: Never 3+ trades in same direction on correlated pairs\n"
            f"```\n\n"
            f"*This is what separates funded traders from blown accounts.*"
        ),
        "color": BRAND_RED,
        "footer": {"text": "Protect the downside. The upside takes care of itself."},
    },

    # ━━━ PROP FIRMS ━━━

    "prop-firms": {
        "title": f"🏦  Prop Firm Discussion",
        "description": (
            f"Everything prop firms. The good, the bad, and the rug pulls.\n\n"
            f"{e('he_bull')} **What to discuss:**\n"
            f"• Prop firm experiences and comparisons\n"
            f"• Rule changes and policy updates\n"
            f"• Which firms are paying, which aren't\n"
            f"• Challenge strategies and tips\n"
            f"• New prop firms entering the market\n\n"
            f"{e('he_alert')} **Community guidelines:**\n"
            f"• Share honest experiences — positive AND negative\n"
            f"• Include evidence when making claims\n"
            f"• No shilling for referral commissions\n"
            f"• Respect that people have different experiences with the same firm"
        ),
        "color": BRAND_BLUE,
        "footer": {"text": "Knowledge shared is capital saved"},
    },

    "challenge-updates": {
        "title": f"⚡  Challenge Updates",
        "description": (
            f"**Track your challenge journey in real-time.**\n\n"
            f"Post daily or weekly updates on your active challenges:\n"
            f"```\n"
            f"🏦 Firm:\n"
            f"📊 Phase: 1 / 2 / Funded\n"
            f"💰 Account size:\n"
            f"📈 Current P&L:\n"
            f"📅 Day: X of Y\n"
            f"🛡️ Hedging: Yes / No\n"
            f"📝 Notes:\n"
            f"```\n\n"
            f"{e('he_fire')} Sharing your journey keeps you accountable and inspires others.\n"
            f"{e('he_shield')} Using Hedge Edge? Tag your updates with `[HEDGED]` so we can track success rates."
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "The community is rooting for you"},
    },

    "payouts": {
        "title": f"💰  Payout Proofs",
        "description": (
            f"**Show. The. Money.** {e('he_profit')}\n\n"
            f"Post your payout confirmations and funded account certificates here.\n\n"
            f"**What to include:**\n"
            f"{e('he_verified')} Screenshot of payout confirmation\n"
            f"{e('he_chartup')} Which firm and account size\n"
            f"{e('he_shield')} Whether you used Hedge Edge\n"
            f"⏱️ How long payout took\n\n"
            f"*Blur sensitive info (email, full name) if you prefer privacy.*\n\n"
            f"{e('he_crown')} Top payout posters get featured in our monthly community spotlight!"
        ),
        "color": BRAND_GOLD,
        "footer": {"text": "Proof > promises"},
    },

    "firm-reviews": {
        "title": f"⭐  Prop Firm Reviews",
        "description": (
            f"**Community-driven prop firm reviews.**\n\n"
            f"Create a thread for each firm you want to review:\n"
            f"```\n"
            f"🏦 Firm name:\n"
            f"⭐ Rating: X/5\n"
            f"💰 Account sizes tried:\n"
            f"📊 Spreads/Execution: \n"
            f"📋 Rules clarity: \n"
            f"💸 Payout speed: \n"
            f"🎧 Support quality: \n"
            f"👍 Pros:\n"
            f"👎 Cons:\n"
            f"🏆 Would recommend: Yes / No / Maybe\n"
            f"```\n\n"
            f"*Honest reviews only. No paid promotions or referral shilling.*"
        ),
        "color": BRAND_BLUE,
        "footer": {"text": "Help the community choose wisely"},
    },

    "brokers": {
        "title": f"🔗  Broker Discussion",
        "description": (
            f"Compare brokers, platforms, and execution quality.\n\n"
            f"{e('he_target')} **Topics:**\n"
            f"• Broker comparisons (spreads, commissions, execution)\n"
            f"• MT4 vs MT5 vs cTrader platform discussion\n"
            f"• Regulation and trust factors\n"
            f"• Broker + prop firm compatibility\n"
            f"• Account setup tips and tricks\n\n"
            f"{e('he_shield')} *For Hedge Edge users: broker setup for hedging is covered in #🔧・setup-guide*"
        ),
        "color": BRAND_DARK,
        "footer": {"text": "Your broker is your infrastructure — choose wisely"},
    },

    # ━━━ HEDGE EDGE ━━━

    "how-it-works": {
        "title": f"{e('he_shield')}  How Hedge Edge Works",
        "description": (
            f"**The complete breakdown of Hedge Edge.**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**The Problem** {e('he_bear')}\n"
            f"Prop firm challenges cost $100-$1000+ per attempt. Most traders fail 2-5 times before passing. "
            f"That's thousands of dollars burned on fees.\n\n"
            f"**The Solution** {e('he_bull')}\n"
            f"Hedge Edge opens a mirror hedge on a separate broker account. If your challenge fails, "
            f"the hedge profit recovers your challenge fee. If you pass, you keep the funded account.\n\n"
            f"**The Math** {e('he_profit')}\n"
            f"```\n"
            f"Without Hedge Edge:\n"
            f"  3 failed attempts × $500 fee = $1,500 lost\n"
            f"  1 pass = funded, but -$1,500 in fees\n"
            f"\n"
            f"With Hedge Edge ($29/mo):\n"
            f"  3 failed attempts × $0 net cost (hedge recovers fees)\n"
            f"  1 pass = funded, only cost $29-87 in subscription\n"
            f"```\n\n"
            f"**Plans:**\n"
            f"{e('he_star')} Free Hedge Guide — learn the strategy\n"
            f"{e('he_shield')} Challenge Shield ($29/mo) — automated hedging\n"
            f"{e('he_diamond')} Multi-Challenge ($59/mo) — multiple accounts *coming soon*\n"
            f"{e('he_crown')} Unlimited ($99/mo) — unlimited accounts *coming soon*\n\n"
            f"Learn more at **hedgedge.info**"
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "Hedge Edge — The smart way to trade prop firm challenges"},
    },

    "setup-guide": {
        "title": f"🔧  Setup Guide",
        "description": (
            f"**Get hedged in under 10 minutes.** {e('he_rocket')}\n\n"
            f"**Step 1 — Sign Up**\n"
            f"Create your account at **hedgedge.info**\n\n"
            f"**Step 2 — Connect Your Broker**\n"
            f"Link your hedging broker account (we'll guide you through it)\n\n"
            f"**Step 3 — Configure Your Challenge**\n"
            f"Enter your prop firm, account size, and challenge parameters\n\n"
            f"**Step 4 — Activate Hedging**\n"
            f"One click to activate. Hedge Edge handles the rest automatically.\n\n"
            f"{e('he_alert')} **Need help?** Ask in #🙋・ask-questions or DM a staff member.\n\n"
            f"*Detailed video tutorials coming soon!*"
        ),
        "color": BRAND_TEAL,
        "footer": {"text": "From zero to hedged in 10 minutes"},
    },

    "feature-requests": {
        "title": f"✨  Feature Requests",
        "description": (
            f"**You ask, we build.** {e('he_fire')}\n\n"
            f"Create a thread for each feature request:\n"
            f"```\n"
            f"✨ Feature: [Name]\n"
            f"📝 Description: [What it does]\n"
            f"🎯 Problem it solves: [Why you need it]\n"
            f"⚡ Priority: Nice-to-have / Important / Critical\n"
            f"```\n\n"
            f"Vote on requests with {e('he_bull')} (want this) or {e('he_bear')} (not needed).\n"
            f"Top-voted features get prioritized on our roadmap.\n\n"
            f"*The Hedge Edge team reviews this channel weekly.*"
        ),
        "color": BRAND_PURPLE,
        "footer": {"text": "Your input shapes the product"},
    },

    "bug-reports": {
        "title": f"🐛  Bug Reports",
        "description": (
            f"Found something broken? Report it here and we'll fix it fast.\n\n"
            f"**Bug report format:**\n"
            f"```\n"
            f"🐛 Bug: [What's wrong]\n"
            f"📱 Platform: [Desktop / Web / EA]\n"
            f"🔄 Steps to reproduce:\n"
            f"  1. ...\n"
            f"  2. ...\n"
            f"  3. ...\n"
            f"📸 Screenshots: [attach if possible]\n"
            f"⚡ Severity: Low / Medium / High / Critical\n"
            f"```\n\n"
            f"{e('he_alert')} **Critical bugs** (affecting live hedges) → also DM @staff immediately.\n"
            f"{e('he_verified')} We aim to acknowledge bugs within 24 hours."
        ),
        "color": BRAND_RED,
        "footer": {"text": "Every bug report makes the product better"},
    },

    "beta-testing": {
        "title": f"🧪  Beta Testing",
        "description": (
            f"**Early access. First to try. First to break things.** {e('he_diamond')}\n\n"
            f"This channel is for beta testers who get early access to new features "
            f"before they go live.\n\n"
            f"{e('he_rocket')} **What beta testers do:**\n"
            f"• Test new features before public release\n"
            f"• Report bugs and edge cases\n"
            f"• Give honest feedback on UX and functionality\n"
            f"• Help shape the final version\n\n"
            f"{e('he_star')} **Perks:**\n"
            f"• First access to every new feature\n"
            f"• Direct line to the dev team\n"
            f"• Beta Tester role badge\n"
            f"• Input on product decisions\n\n"
            f"*Want to become a beta tester? React with {e('he_shield')} in #🎭・roles*"
        ),
        "color": BRAND_PURPLE,
        "footer": {"text": "Break it before we ship it"},
    },

    # ━━━ EDUCATION ━━━

    "resources": {
        "title": f"📚  Learning Resources",
        "description": (
            f"**Free resources to level up your trading.** {e('he_chartup')}\n\n"
            f"This is the community library. Share and find:\n"
            f"• Trading tutorials and video courses\n"
            f"• PDF guides and cheat sheets\n"
            f"• Useful tools and calculators\n"
            f"• Backtesting templates\n"
            f"• Economic calendar links\n\n"
            f"{e('he_verified')} **Posting guidelines:**\n"
            f"• Only share free, legal resources\n"
            f"• No pirated courses or paid content shared for free\n"
            f"• Add a brief description of what you're sharing\n"
            f"• Tag the category: `[VIDEO]` `[PDF]` `[TOOL]` `[GUIDE]`"
        ),
        "color": BRAND_BLUE,
        "footer": {"text": "Knowledge is the ultimate edge"},
    },

    "hedge-guide": {
        "title": f"{e('he_shield')}  The Hedge Edge Guide",
        "description": (
            f"**The free, comprehensive guide to prop firm hedging.**\n\n"
            f"This is the complete knowledge base on how hedging works, why it works, "
            f"and how to implement it — whether you use Hedge Edge or not.\n\n"
            f"**📖 What's covered:**\n"
            f"• What is challenge hedging?\n"
            f"• The math behind fee recovery\n"
            f"• Setting up a hedging broker account\n"
            f"• Position sizing for hedges\n"
            f"• Common mistakes and how to avoid them\n"
            f"• Hedge vs. no-hedge: real data comparison\n\n"
            f"{e('he_profit')} **Download the full guide:**\n"
            f"Visit **hedgedge.info** → Free Hedge Guide\n\n"
            f"*Questions about the guide? Ask in #🙋・ask-questions*"
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "Free education — no strings attached"},
    },

    "ask-questions": {
        "title": f"🙋  Ask Questions",
        "description": (
            f"**No question is too basic.** {e('he_welcome')}\n\n"
            f"Whether you're completely new to trading or a funded veteran confused about "
            f"something specific — ask here.\n\n"
            f"{e('he_verified')} **Good questions include:**\n"
            f"• How does hedging work with [specific prop firm]?\n"
            f"• What lot size should I use for a $100K challenge?\n"
            f"• Is it possible to hedge with [broker]?\n"
            f"• How do I calculate my daily drawdown limit?\n\n"
            f"{e('he_alert')} **Before asking:**\n"
            f"1. Check #📖・hedge-guide — your answer might be there\n"
            f"2. Search the channel — someone may have asked before\n"
            f"3. Be specific — \"help me\" is hard to answer; include details\n\n"
            f"*Community members and staff both answer here. Be patient and kind.*"
        ),
        "color": BRAND_TEAL,
        "footer": {"text": "The only dumb question is the one you didn't ask"},
    },

    "books": {
        "title": f"📕  Book Recommendations",
        "description": (
            f"**Books that make better traders.** {e('he_crown')}\n\n"
            f"Share your must-reads:\n"
            f"```\n"
            f"📕 Title:\n"
            f"✍️ Author:\n"
            f"⭐ Rating: X/5\n"
            f"🎯 Best for: [beginners / intermediate / advanced]\n"
            f"💡 Key takeaway:\n"
            f"```\n\n"
            f"**Community Favorites:**\n"
            f"• *Trading in the Zone* — Mark Douglas\n"
            f"• *Reminiscences of a Stock Operator* — Edwin Lefèvre\n"
            f"• *Market Wizards* — Jack D. Schwager\n"
            f"• *The Disciplined Trader* — Mark Douglas\n\n"
            f"*Add yours below!*"
        ),
        "color": BRAND_PURPLE,
        "footer": {"text": "Read more, lose less"},
    },

    # ━━━ PREMIUM ━━━

    "premium-chat": {
        "title": f"{e('he_crown')}  Premium Chat",
        "description": (
            f"**Welcome to the inner circle.** {e('he_diamond')}\n\n"
            f"This channel is exclusively for Challenge Shield subscribers and above.\n\n"
            f"**What you get here:**\n"
            f"• Direct access to the Hedge Edge team\n"
            f"• Priority support for your hedge setups\n"
            f"• Advanced strategy discussions\n"
            f"• Early announcements before public channels\n"
            f"• Network with other serious traders\n\n"
            f"{e('he_shield')} Thank you for supporting Hedge Edge. Your subscription keeps us building.\n\n"
            f"*Not a subscriber yet? Check out plans at **hedgedge.info***"
        ),
        "color": BRAND_GOLD,
        "footer": {"text": "Hedge Edge Premium — The serious traders' room"},
    },

    "premium-signals": {
        "title": f"📡  Premium Signals",
        "description": (
            f"**Subscriber-only hedging alerts and market insights.** {e('he_fire')}\n\n"
            f"What gets posted here:\n"
            f"{e('he_alert')} Hedging opportunity alerts\n"
            f"{e('he_chartup')} High-probability trade setups\n"
            f"{e('he_target')} Optimal hedge entry/exit timing\n"
            f"{e('he_shield')} Risk management recommendations\n\n"
            f"{e('he_alert')} **Disclaimer:** Signals are educational and not financial advice. "
            f"Always do your own analysis and manage your own risk.\n\n"
            f"*Turn on notifications for this channel: 🔔*"
        ),
        "color": BRAND_GREEN,
        "footer": {"text": "The edge behind the edge"},
    },

    "premium-resources": {
        "title": f"🔐  Premium Resources",
        "description": (
            f"**Subscriber-only tools, templates, and deep dives.** {e('he_lock')}\n\n"
            f"**Available resources:**\n"
            f"{e('he_shield')} EA configuration templates\n"
            f"{e('he_chartup')} Advanced position sizing calculators\n"
            f"{e('he_profit')} Fee recovery optimization spreadsheets\n"
            f"{e('he_diamond')} Broker comparison matrices\n"
            f"{e('he_star')} Video tutorials (advanced)\n\n"
            f"*New resources added monthly. Suggestions? Drop them in #💡・suggestions*"
        ),
        "color": BRAND_GOLD,
        "footer": {"text": "Premium tools for premium traders"},
    },

    # ━━━ STAFF ━━━

    "staff-chat": {
        "title": f"🔒  Staff Chat",
        "description": (
            f"**Internal communication channel.**\n\n"
            f"Team coordination, strategy discussion, and operational planning.\n"
            f"Everything here is confidential."
        ),
        "color": BRAND_DARK,
        "footer": {"text": "Hedge Edge — Internal"},
    },

    "mod-logs": {
        "title": f"📋  Moderation Logs",
        "description": (
            f"Automated log of all moderation actions.\n\n"
            f"• Member joins/leaves\n"
            f"• Bans, kicks, and timeouts\n"
            f"• Deleted messages (if bot tracks)\n"
            f"• Role changes\n"
            f"• Audit trail for transparency"
        ),
        "color": BRAND_DARK,
        "footer": {"text": "Transparency in moderation"},
    },

    "bot-commands": {
        "title": f"🤖  Bot Commands",
        "description": (
            f"Test bot commands here. Keep the noise out of public channels.\n\n"
            f"All admin, moderation, and utility bot commands should be run in this channel."
        ),
        "color": BRAND_DARK,
        "footer": {"text": "Bots only beyond this point"},
    },
}


# ─── Send all messages ────────────────────────────────────────────

print(f"Sending branded messages to {len(MESSAGES)} channels...\n")

success = 0
failed = 0

for channel_name, embed_data in MESSAGES.items():
    result = send_embed(channel_name, embed_data)
    if result:
        success += 1
    else:
        failed += 1
    time.sleep(1.5)

print(f"\n{'=' * 50}")
print(f"Done! {success} messages sent & pinned, {failed} failed.")
