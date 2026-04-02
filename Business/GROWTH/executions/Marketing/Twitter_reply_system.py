#!/usr/bin/env python3
"""
Hedge Edge - Twitter Auto-Reply Bot v2
=======================================
Reads unreplied leads from Notion, generates contextual replies via Groq,
posts via nodriver with full anti-detection humanization, updates Notion.

Anti-detection features:
  - Human-like character-by-character typing (variable speed, bursts, pauses)
  - Bezier curve mouse movements with jitter on clicks
  - Pre-reply reading simulation (scroll, pause, read)
  - Session warmup (browse timeline before replying)
  - Gaussian-distributed intervals between replies (2-6 min + random long pauses)
  - Fatigue modeling (slower as session progresses)
  - Hourly velocity cap (20/hr soft limit)
  - Content variation (natural noise on replies)

Usage:
  python scripts/tw_reply_v2.py --action preview          # Preview replies
  python scripts/tw_reply_v2.py --action run               # Post replies
  python scripts/tw_reply_v2.py --action run --limit 50    # Post up to 50
  python scripts/tw_reply_v2.py --action status            # Show stats
"""

import asyncio, json, os, sys, argparse, time, requests, random
from datetime import datetime, timezone, date

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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(_WS_ROOT, ".env"))
load_dotenv(os.path.join(_WS_ROOT, "Business", "GROWTH", "resources", ".env"), override=True)

# Import humanization layer
from tw_humanize import (
    human_delay, reply_interval, typing_speed, reading_pause,
    jitter_coords, bezier_points, human_type, human_mouse_move,
    simulate_reading, session_warmup, add_natural_noise,
    ReplySession, HOURLY_SOFT_LIMIT, check_velocity,
    between_reply_actions, session_break_browse,
    browse_feed, like_random_tweet
)

#  Constants 
TWITTER_LEADS_DB = "310652ea-6c6d-81de-8a89-e65f52bfa97a"
PROFILE_DIR = os.environ.get(
    "CHROME_PROFILE_DIR",
    os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "HedgeEdge_Twitter_Profile"),
)
DAILY_LIMIT = 200  # Target: 200 replies/day in 4 sessions

# Reply safety: block these patterns from ever being posted
BLOCKED_PATTERNS = [
    'hedgedge', 'hedge edge', 'hedg edge',
    'http', 'https', 'www.',
    'check out', 'check this', 'try this',
    'dm me', 'dm for', 'message me',
    'link in bio', 'link in my',
    'sign up', 'signup', 'subscribe',
    '#', '@hedg',
]

# Brand handles to never reply to
EXCLUDED_HANDLES = {
    'andreeatrade', 'breakouthunter', 'dhruvtradesfx',
    'funded_trading', 'itradepropfirm', 'propfirmmedia',
    'propfirmshunter', 'tradergalt', 'hedgedge',
}

# Off-topic / NSFW tweet content filter
# Tweets matching these patterns are NOT about trading and should be skipped.
# Catches misfires where keywords like "challenge" or "failed" match non-trading tweets.
NSFW_SKIP_PATTERNS = [
    'bbc', 'nsfw', 'onlyfans', 'porn', 'nude', 'nudes', 'sex',
    'cum', 'dick', 'pussy', 'boob', 'sissy', 'sissies', 'fetish',
    'kink', 'bdsm', 'escort', 'stripper', 'milf', 'slut', 'whore',
    'hentai', 'xxx', 'lewd', '18+', 'adult content',
    'whiteboi', 'cuck', 'domme', 'femdom', 'findom',
]

# Non-trading context patterns — tweets clearly unrelated to finance/trading
OFF_TOPIC_PATTERNS = [
    'weight loss', 'diet challenge', 'fitness challenge', 'gym challenge',
    'cooking challenge', 'dance challenge', 'tiktok challenge',
    'giveaway', 'follow for follow', 'f4f', 'rt to win',
    'astrology', 'zodiac', 'horoscope',
]


def is_off_topic(tweet_text):
    """Return (True, reason) if tweet is NSFW or off-topic, else (False, None)."""
    text_lower = tweet_text.lower()
    for pat in NSFW_SKIP_PATTERNS:
        if pat in text_lower:
            return True, f"NSFW content (matched '{pat}')"
    for pat in OFF_TOPIC_PATTERNS:
        if pat in text_lower:
            return True, f"Off-topic (matched '{pat}')"
    return False, None

BATCH_SIZE = 50       # Replies per session before taking a break
SESSION_BREAK_MIN = 15  # Base break min (used for warmup browse)

# --- Randomised session spacing ---
# Sessions are spread across a shorter window with varied but compact breaks
# so the bot finishes its run within a few hours each day.
SESSION_SPREAD_HOURS = 5    # Rough total runtime target (sessions + gaps)
MIN_BREAK_MIN = 20          # Shortest break between sessions (20 min)
MAX_BREAK_MIN = 45          # Longest break between sessions (45 min)
WARMUP_BROWSE_MIN = 4       # Organic browse at the start of each break (before idling)


def generate_session_schedule(n_sessions, total_spread_hrs=None):
    """Generate randomised break durations between sessions.

    Returns a list of (n_sessions - 1) break durations in minutes.
    The breaks are randomised so the daily pattern is never identical.

    Algorithm:
        1. Estimate total active reply time  (n_sessions * ~120 min each)
        2. Remaining time = spread target - active time
        3. Divide remaining time into (n_sessions-1) breaks with jitter
        4. Shuffle and clip to min/max bounds

    Example for 3 sessions over ~10h:
        Active: ~6h (3  2h) -> Breaks: ~4h total -> 2 breaks of ~2h each (jitter)
    """
    import random as _rng

    spread = (total_spread_hrs or SESSION_SPREAD_HOURS) * 60  # total minutes
    n_breaks = n_sessions - 1
    if n_breaks <= 0:
        return []

    # Estimate active time per session (~2h for 40-50 replies at 3min avg)
    est_active_per_session = 120  # minutes
    total_active = n_sessions * est_active_per_session
    total_break_budget = max(spread - total_active, n_breaks * MIN_BREAK_MIN)

    # Split budget into n_breaks with random weights
    weights = [_rng.uniform(0.5, 2.0) for _ in range(n_breaks)]
    w_sum = sum(weights)
    breaks = [(w / w_sum) * total_break_budget for w in weights]

    # Add daily jitter: 15 min per break
    breaks = [b + _rng.uniform(-15, 15) for b in breaks]

    # Clip to bounds
    breaks = [max(MIN_BREAK_MIN, min(MAX_BREAK_MIN, b)) for b in breaks]

    # Shuffle so the pattern isn't predictable
    _rng.shuffle(breaks)

    return [round(b) for b in breaks]
NUM_SESSIONS = 4      # Default number of sessions per run

# Graduated calibration ramp (day -> max replies)
GRADUATED_RAMP = {
    1: 25,    # Day 1: 1 session of 25
    2: 50,    # Day 2: 2 sessions of 25
    3: 100,   # Day 3: 2 sessions of 50
    4: 150,   # Day 4: 3 sessions of 50
    5: 200,   # Day 5: 4 sessions of 50 (full target)
}

#  Notion helpers 
def notion_headers():
    return {
        "Authorization": f"Bearer {os.getenv('NOTION_API_KEY')}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

def get_unreplied_leads(limit=100):
    """Fetch unreplied leads sorted by Priority (Pain Point/Seeker first)."""
    h = notion_headers()
    payload = {
        "filter": {
            "and": [
                {"property": "DM Status", "select": {"is_empty": True}},
            ]
        },
        "sorts": [
            {"property": "Priority", "direction": "ascending"},
            {"property": "Tweet Date", "direction": "descending"},
        ],
        "page_size": min(limit, 100),
    }

    results = []
    start_cursor = None
    while len(results) < limit:
        if start_cursor:
            payload["start_cursor"] = start_cursor
        r = requests.post(
            f"https://api.notion.com/v1/databases/{TWITTER_LEADS_DB}/query",
            headers=h, json=payload, timeout=15
        )
        r.raise_for_status()
        data = r.json()

        for page in data.get("results", []):
            props = page["properties"]
            handle_parts = props.get("Handle", {}).get("title", [])
            handle = "".join(t.get("plain_text", "") for t in handle_parts).lstrip("@").lower()

            # Skip excluded handles
            if handle in EXCLUDED_HANDLES:
                continue

            text_parts = props.get("Tweet Text", {}).get("rich_text", [])
            tweet_text = "".join(t.get("plain_text", "") for t in text_parts)

            # Skip NSFW / off-topic tweets and mark them as false positives
            off_topic, reason = is_off_topic(tweet_text)
            if off_topic:
                print(f"    SKIP @{handle}: {reason}")
                update_lead_status(
                    page["id"], "Skipped",
                    f"[Auto-filtered] {reason}"
                )
                continue

            url = props.get("Tweet URL", {}).get("url", "")

            priority_sel = props.get("Priority", {}).get("select")
            priority = priority_sel.get("name", "Low") if priority_sel else "Low"

            query_sel = props.get("Search Query", {}).get("select")
            query = query_sel.get("name", "") if query_sel else ""

            notes_parts = props.get("Notes", {}).get("rich_text", [])
            notes = "".join(t.get("plain_text", "") for t in notes_parts)

            # Extract category from Notes field
            category = "General"
            if notes.startswith("[") and "]" in notes:
                category = notes.split("]")[0][1:]

            results.append({
                "page_id": page["id"],
                "handle": handle,
                "tweet_text": tweet_text,
                "tweet_url": url,
                "priority": priority,
                "query": query,
                "category": category,
                "notes": notes,
            })

        if not data.get("has_more") or len(results) >= limit:
            break
        start_cursor = data["next_cursor"]

    return results[:limit]


def update_lead_status(page_id, status, reply_text=""):
    """Update a lead's DM Status and Notes in Notion."""
    h = notion_headers()
    props = {
        "DM Status": {"select": {"name": status}},
        "DM Date": {"date": {"start": date.today().isoformat()}},
    }
    if reply_text:
        props["Notes"] = {"rich_text": [{"text": {"content": reply_text[:2000]}}]}

    r = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=h, json={"properties": props}, timeout=15
    )
    return r.status_code == 200


#  Category-driven reply generation 

def get_category_prompt(category, handle, tweet_text):
    """Generate LLM prompt based on lead CATEGORY (not keyword matching).
    
    Category-driven approach (from our statistical analysis):
      Pain Point  -> T3-LEAD: Reference their specific pain, show hedging as solution
      Seeker      -> T3-LEAD: Direct answer about reverse positions
      Hedging Disc -> T2-SEED: Share advanced insight (they already know hedging)
      General     -> T1-ENGAGE: Pure value, no hedging mention
    """
    base_rules = """RULES (strict):
- Max 200 characters
- Sound like a real trader, casual lowercase
- NO hashtags, NO links, NO emojis
- NO product names, company names, or calls to action
- NO "check out", "DM me", "link in bio"
- Single reply, no line breaks
- Be genuine and conversational"""

    # Rotating approach angles prevent repetitive replies
    pain_approaches = [
        "share that you protect your capital on retakes now",
        "mention you found a way to not lose money on failed challenges",
        "say you hedge your risk on a personal account now",
        "hint that failing challenges doesnt cost you money anymore",
        "share that you run a safety net on your own broker for exactly this",
    ]

    seeker_approaches = [
        "briefly explain you run reverse positions on a personal broker",
        "share that you mirror trades in reverse on your own account",
        "mention you use a personal broker to catch the other side of your prop trades",
    ]

    hedging_approaches = [
        "share a specific detail about your hedging setup (speed, automation, timing)",
        "mention what changed for you since you started hedging (less stress, consistent paydays)",
        "add to the conversation with your execution experience (which pairs, how fast)",
        "share one concrete result from hedging (recovered X% of a failed challenge)",
    ]

    if category == "Pain Point":
        approach = random.choice(pain_approaches)
        return f"""{base_rules}

You are a prop firm trader who has been through the same pain of failing challenges.
Reply to this tweet empathetically. {approach}.
Sound like youve been there and found a workaround.

Tweet by @{handle}: "{tweet_text[:500]}"

Reply:"""

    elif category == "Seeker":
        approach = random.choice(seeker_approaches)
        return f"""{base_rules}

This trader is looking for hedging solutions. You do this already.
Reply with a direct but casual answer. {approach}.
Be helpful, not salesy.

Tweet by @{handle}: "{tweet_text[:500]}"

Reply:"""

    elif category == "Hedging Discussion":
        approach = random.choice(hedging_approaches)
        return f"""{base_rules}

This trader already knows about hedging. Dont explain the basics.
Reply as a fellow hedger adding to the conversation. {approach}.
Sound experienced and knowledgeable.

Tweet by @{handle}: "{tweet_text[:500]}"

Reply:"""

    else:  # General
        return f"""{base_rules}

You are a prop firm trader casually replying to another trader.
Be helpful, share a quick opinion or experience. Pure value, zero agenda.
Do NOT mention hedging, capital protection, or any product.

Tweet by @{handle}: "{tweet_text[:500]}"

Reply:"""


def generate_reply(handle, tweet_text, category):
    """Generate a reply using Groq LLM with category-driven prompts.
    
    Handles 429 rate limits with exponential backoff and falls back to
    a smaller model (llama-3.1-8b-instant) if the primary model's daily
    token quota is exhausted.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, category

    from groq import Groq
    client = Groq(api_key=api_key)

    prompt = get_category_prompt(category, handle, tweet_text)

    # Model priority: try primary first, then fallback
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    max_retries = 3
    reply = None

    for model in models:
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.75,
                    max_tokens=100,
                )
                reply = resp.choices[0].message.content.strip().strip('"').strip("'")
                if attempt > 0 or model != models[0]:
                    print(f"    (used {model}, attempt {attempt+1})")
                break  # success — exit retry loop
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate_limit" in err_str:
                    # Extract wait time from error if available
                    import re as _re_wait
                    wait_match = _re_wait.search(r'try again in ([\d.]+)s', err_str)
                    if wait_match:
                        wait_sec = min(float(wait_match.group(1)), 300)  # cap at 5 min
                    else:
                        wait_sec = (attempt + 1) * 60  # 60s, 120s, 180s
                    
                    if "TPD" in err_str:
                        # Daily limit hit — skip straight to fallback model
                        print(f"    Rate limit (daily TPD) on {model}, switching to fallback...")
                        break
                    else:
                        print(f"    Rate limit on {model}, waiting {wait_sec:.0f}s (attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_sec)
                else:
                    print(f"    Groq error: {e}")
                    return None, category
        
        # If we got a reply, stop trying models
        if reply is not None:
            break
    
    if reply is None:
        print(f"    All Groq models rate-limited, skipping @{handle}")
        return None, category

    # Safety filter
    reply_lower = reply.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in reply_lower:
            print(f"    BLOCKED: Reply contained '{pattern}' - regenerating")
            try:
                resp2 = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=100,
                )
                reply = resp2.choices[0].message.content.strip().strip('"').strip("'")
            except Exception:
                pass  # keep original reply if retry fails
            break

    # Add natural variation
    reply = add_natural_noise(reply)

    # Quality check: catch garbled words from high-temp LLM
    import re as _re
    words = _re.findall(r"[a-zA-Z]+", reply)
    if words:
        garbled_count = 0
        for w in words:
            wl = w.lower()
            if len(wl) >= 5:
                vowels = sum(1 for c in wl if c in 'aeiou')
                consonants = len(wl) - vowels
                if vowels == 0 or (consonants / max(vowels, 1) > 4.5):
                    garbled_count += 1
                if _re.search(r'[^aeiou]{4,}', wl):
                    common_clusters = {'rhythm','strengths','through','thought','brought','straight','ights','ength','ngths','tching','tchng'}
                    if not any(cc in wl for cc in common_clusters):
                        garbled_count += 1

        if garbled_count >= 2:
            print(f"    QUALITY BLOCK: {garbled_count} garbled words - regenerating at low temp...")
            try:
                resp3 = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,
                    max_tokens=100,
                )
                reply = resp3.choices[0].message.content.strip().strip(chr(34)).strip(chr(39))
                reply = add_natural_noise(reply)
            except Exception:
                pass  # keep original if retry fails

    # Enforce length limit
    if len(reply) > 240:
        reply = reply[:237] + "..."

    return reply, category


#  Humanized reply posting 

async def post_reply_humanized(tweet_url, reply_text, page):
    """Navigate to tweet and post reply with full human simulation.
    
    Sequence:
    1. Navigate to tweet URL
    2. Wait for page load
    3. Simulate reading the tweet (scroll, pause)
    4. Move mouse naturally to reply box and click
    5. Type reply character-by-character with human timing
    6. Brief pause (re-reading what we typed)
    7. Move mouse to Reply button and click with jitter
    8. Wait and verify
    """
    from nodriver.cdp import input_ as cdp_input

    # 1. Navigate
    page = await page._browser.get(tweet_url)
    await asyncio.sleep(random.uniform(3.0, 5.0))

    # 2. Wait for tweet to load
    loaded = False
    for _ in range(20):
        has_tweet = await page.evaluate(
            'document.querySelector("[data-testid=\\"tweetText\\"]") ? "yes" : ""'
        )
        if has_tweet:
            loaded = True
            break
        await asyncio.sleep(0.5)

    if not loaded:
        return False, "Tweet page did not load"

    # 3. Simulate reading the tweet
    tweet_visible = await page.evaluate('''
        (function() {
            const el = document.querySelector('[data-testid="tweetText"]');
            return el ? el.textContent : "";
        })()
    ''') or ""
    await simulate_reading(page, tweet_visible)

    # 4. Find and click reply box with human mouse movement
    reply_box_pos = await page.evaluate('''
        (function() {
            const box = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (box) {
                const r = box.getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)});
            }
            const inputs = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
            if (inputs.length > 0) {
                const r = inputs[0].getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)});
            }
            return "";
        })()
    ''')

    if not reply_box_pos:
        return False, "Could not find reply box"

    coords = json.loads(reply_box_pos)
    await human_mouse_move(page, coords['x'], coords['y'])
    await asyncio.sleep(human_delay(0.3, 0.8))

    # Focus the textbox
    await page.evaluate('''
        (function() {
            const box = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (box) { box.click(); box.focus(); return; }
            const inputs = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
            if (inputs.length > 0) { inputs[0].click(); inputs[0].focus(); }
        })()
    ''')
    await asyncio.sleep(human_delay(0.5, 1.2))

    # 5. Type reply with human-like keystrokes
    await human_type(page, reply_text)
    await asyncio.sleep(human_delay(0.3, 0.6))

    # 6. Verify text was entered
    typed = await page.evaluate('''
        (function() {
            const boxes = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
            for (const b of boxes) { if (b.textContent.length > 0) return b.textContent.length; }
            return 0;
        })()
    ''')

    if not typed:
        return False, "Reply text was not entered"

    # 7. Brief pause to "re-read" what we typed
    await asyncio.sleep(human_delay(0.8, 2.5))

    # 8. Find Reply button and click with human mouse movement
    btn_pos = await page.evaluate('''
        (function() {
            const btns = document.querySelectorAll('[data-testid="tweetButtonInline"]');
            if (btns.length > 0) {
                const r = btns[0].getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)});
            }
            const allBtns = Array.from(document.querySelectorAll('[role="button"]')).filter(
                e => e.innerText.trim() === "Reply" || e.innerText.trim() === "Post"
            );
            if (allBtns.length > 0) {
                const r = allBtns[0].getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)});
            }
            return "";
        })()
    ''')

    if not btn_pos:
        return False, "Could not find Reply/Post button"

    btn_coords = json.loads(btn_pos)

    # Move from reply box area to button area naturally
    await human_mouse_move(
        page, btn_coords['x'], btn_coords['y'],
        start_x=coords['x'] + random.randint(-20, 20),
        start_y=coords['y'] + random.randint(-10, 10)
    )

    # 9. Wait for reply to submit
    await asyncio.sleep(random.uniform(3.0, 5.0))

    # 10. VERIFY the reply was actually posted (3-step confirmation)
    # Check A: Reply textbox should be empty after successful post
    textbox_len = await page.evaluate("""
        (function() {
            const boxes = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
            for (const b of boxes) { if (b.textContent.length > 0) return b.textContent.length; }
            return 0;
        })()
    """)

    if textbox_len and textbox_len > 5:
        # Textbox still has text = reply was NOT submitted
        # Try clicking the button one more time
        print(f"    RETRY: Textbox still has text ({textbox_len} chars), re-clicking...")
        await human_mouse_move(
            page, btn_coords['x'], btn_coords['y'],
            start_x=btn_coords['x'] + random.randint(-30, 30),
            start_y=btn_coords['y'] + random.randint(-20, 20)
        )
        await asyncio.sleep(random.uniform(3.0, 5.0))

        # Check again
        textbox_len2 = await page.evaluate("""
            (function() {
                const boxes = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
                for (const b of boxes) { if (b.textContent.length > 0) return b.textContent.length; }
                return 0;
            })()
        """)
        if textbox_len2 and textbox_len2 > 5:
            return False, f"Reply button click failed - textbox still has {textbox_len2} chars"

    # Check B: Look for error messages on page
    body_text = await page.evaluate("document.body?.innerText?.substring(0,1000) || \"\"")
    error_phrases = ["error", "try again", "something went wrong", "rate limit",
                     "unable to", "this request"]
    for phrase in error_phrases:
        if phrase in body_text.lower():
            return False, f"Twitter error: \'{phrase}\'"

    # Check C: Verify our reply text appears on the page
    reply_snippet = reply_text[:40].replace("'", "").replace('"', '')
    found_reply = await page.evaluate(
        '(function() {'
        '  const tweets = document.querySelectorAll(\'[data-testid="tweetText"]\');'
        '  for (const t of tweets) {'
        '    if (t.textContent.includes("' + reply_snippet + '")) return true;'
        '  }'
        '  return false;'
        '})()'
    )

    if found_reply:
        return True, "Reply posted and verified on page"

    # If textbox is empty but we can't find reply text, likely succeeded
    # (Twitter may scroll or reply is below fold)
    if not textbox_len or textbox_len == 0:
        return True, "Reply likely posted (textbox cleared)"

    return False, "Reply could not be verified"


#  Main workflow
# ============================================================================
#  Main workflow  Session-based with behavioral camouflage
# ============================================================================

async def run_session(browser, page, reply_batch, session_num, total_sessions):
    """Run one reply session (typically 50 replies).

    Between each reply:
    1. Navigate to tweet URL (direct navigation is fine)
    2. Read tweet, type reply, post (existing post_reply_humanized)
    3. Do organic browsing (feed scroll, like, profile visit)
    4. Wait human-like interval

    Returns (posted, failed) counts.
    """
    posted = 0
    failed = 0
    session = ReplySession(daily_limit=len(reply_batch) + 10)

    print(f"\n{'=' * 60}")
    print(f"  SESSION {session_num}/{total_sessions}  {len(reply_batch)} replies")
    print(f"{'=' * 60}")

    for i, rp in enumerate(reply_batch):
        if not session.can_reply():
            print(f"\n    Session safety limit reached")
            break

        print(f"\n  [{i+1}/{len(reply_batch)}] @{rp['handle']} [{rp['category']}]")

        # --- Navigate to tweet ---
        if not rp.get('tweet_url'):
            print(f"    No tweet URL - navigating to profile...")
            page = await browser.get(f"https://x.com/{rp['handle']}")
            await asyncio.sleep(random.uniform(3, 5))

            found_url = await page.evaluate(
                '(function() {'
                '  var links = document.querySelectorAll(\'a[href*="/' + rp["handle"] + '/status/"]\');'
                '  for (var j = 0; j < links.length; j++) {'
                '    var href = links[j].getAttribute("href");'
                '    if (href && href.match(/\\/status\\/\\d+$/)) return "https://x.com" + href;'
                '  }'
                '  return "";'
                '})()'
            )

            if found_url:
                rp['tweet_url'] = found_url
                print(f"    Found: {found_url}")
            else:
                print(f"    SKIP: Could not find tweet URL")
                failed += 1
                session.record_error()
                continue

        # --- Post the reply ---
        success, msg = await post_reply_humanized(rp['tweet_url'], rp['reply'], page)

        if success:
            print(f"    POSTED: {rp['reply'][:60]}...")
            updated = update_lead_status(
                rp['page_id'], "Replied",
                f"[{rp['category']}] REPLIED: {rp['reply']}"
            )
            print(f"    Notion: {'updated' if updated else 'FAILED'}")
            posted += 1
            session.record_reply()
        else:
            print(f"    FAILED: {msg}")
            update_lead_status(rp['page_id'], "Reply Failed", f"Error: {msg}")
            failed += 1
            session.record_error()

        # --- Organic behavior between replies ---
        if i < len(reply_batch) - 1 and session.can_reply():
            # First: do organic browsing (scroll feed, like, visit profiles)
            action_desc = await between_reply_actions(page)
            print(f"    Organic: {action_desc}")

            # Then: human-like delay before next reply
            delay = session.next_delay()
            print(f"    Next in {delay:.0f}s ({delay/60:.1f} min)...")
            await asyncio.sleep(delay)

    return posted, failed


async def run_replies(limit=200, batch_size=50, sessions=4, break_min=15,
                      dry_run=False, graduated_day=0):
    """Main reply workflow with session-based architecture.

    Architecture:
    - Fetches all leads upfront, generates all replies
    - Splits into sessions of batch_size replies each
    - Between sessions: 15-20 min break with organic browsing
    - Between replies: organic feed browsing, liking, profile visits
    - Direct URL navigation to tweets (organic behavior surrounds it)

    Args:
        limit: Total replies for this run
        batch_size: Replies per session
        sessions: Max number of sessions
        break_min: Minutes between sessions
        dry_run: Preview mode (no posting)
        graduated_day: If > 0, override limit from calibration ramp
    """
    # Graduated calibration override
    if graduated_day > 0:
        if graduated_day in GRADUATED_RAMP:
            limit = GRADUATED_RAMP[graduated_day]
            print(f"  Graduated mode: Day {graduated_day} -> {limit} replies")
        else:
            limit = GRADUATED_RAMP[max(GRADUATED_RAMP.keys())]
            print(f"  Graduated mode: Day {graduated_day} (capped) -> {limit} replies")

    actual_sessions = min(sessions, -(-limit // batch_size))  # ceil division
    actual_batch = min(batch_size, limit)

    # Generate randomised session schedule (different every day)
    session_breaks = generate_session_schedule(actual_sessions)
    total_break_min = sum(session_breaks) if session_breaks else 0



    print("=" * 60)
    mode = "[PREVIEW]" if dry_run else "[LIVE]"
    print(f"  Hedge Edge Twitter Reply Bot v3 {mode}")
    print(f"  Target: {limit} replies | {actual_sessions} sessions x {actual_batch}")
    print(f"  Spacing: randomised | Camouflage: ON")
    if graduated_day > 0:
        print(f"  Graduated calibration: Day {graduated_day}")
    if session_breaks:
        est_total_h = (total_break_min + actual_sessions * 120) / 60
        print(f"  Schedule: ~{est_total_h:.1f}h total runtime")
        for bi, bk in enumerate(session_breaks):
            print(f"    Session {bi+1} -> [{bk} min break ({bk/60:.1f}h)] -> Session {bi+2}")
    print("=" * 60)

    # Step 1: Fetch leads
    print(f"\n[1] Fetching unreplied leads from Notion...")
    leads = get_unreplied_leads(limit)
    print(f"    Found {len(leads)} unreplied leads")

    if not leads:
        print("    No leads to reply to.")
        return

    cat_counts = {}
    for lead in leads:
        c = lead['category']
        cat_counts[c] = cat_counts.get(c, 0) + 1
    print(f"    Categories: {cat_counts}")

    # Step 2: Generate ALL replies upfront (avoids Groq calls during sessions)
    print(f"\n[2] Generating replies via Groq...")
    reply_plan = []
    for lead in leads:
        reply, cat = generate_reply(lead['handle'], lead['tweet_text'], lead['category'])
        if reply:
            reply_plan.append({**lead, 'reply': reply, 'tier': cat})
            print(f"    @{lead['handle']:<22} [{cat:<20}] -> {reply[:60]}...")

    print(f"\n    Generated {len(reply_plan)} replies")

    if dry_run:
        print(f"\n[PREVIEW] Use --action run to post these replies.")
        # Show session breakdown
        for s in range(actual_sessions):
            start = s * actual_batch
            end = min(start + actual_batch, len(reply_plan))
            if start >= len(reply_plan):
                break
            print(f"    Session {s+1}: replies {start+1}-{end}")
        return

    # Step 3: Launch browser
    print(f"\n[3] Launching browser...")
    import nodriver as uc
    import glob as _glob

    # Kill any leftover browser processes and clean lock files
    os.system("pkill -9 -f chromium 2>/dev/null || true")
    await asyncio.sleep(1)
    for _lock in _glob.glob(os.path.join(PROFILE_DIR, "Singleton*")):
        try: os.remove(_lock)
        except: pass

    browser = None
    for _attempt in range(3):
        try:
            browser = await uc.start(
                headless=False,
                sandbox=False,
                no_sandbox=True,
                user_data_dir=PROFILE_DIR,
                browser_args=[
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                    "--window-size=1280,720",
                ],
            )
            break
        except Exception as _e:
            print(f"    Browser start attempt {_attempt+1}/3 failed: {_e}")
            os.system("pkill -9 -f chromium 2>/dev/null || true")
            await asyncio.sleep(3)
            for _lock in _glob.glob(os.path.join(PROFILE_DIR, "Singleton*")):
                try: os.remove(_lock)
                except: pass

    if not browser:
        print("    Could not start browser after 3 attempts")
        return

    # Cookie injection: if COOKIE_FILE is set, inject cookies via CDP
    cookie_file = os.environ.get("COOKIE_FILE")
    if cookie_file and os.path.exists(cookie_file):
        from nodriver.cdp import network as cdp_network
        print(f"    Injecting cookies from {cookie_file}...")
        with open(cookie_file) as _cf:
            _raw = json.load(_cf)
        _targets = ["x.com", "twitter.com"]
        _tw_cookies = [c for c in _raw if any(d in c.get("domain", "") for d in _targets)]
        _ss_map = {
            "Strict": cdp_network.CookieSameSite.STRICT,
            "Lax": cdp_network.CookieSameSite.LAX,
            "None": cdp_network.CookieSameSite.NONE,
        }
        # Navigate to x.com first so cookies are set in correct context
        page = await browser.get("https://x.com")
        await asyncio.sleep(3)
        _params = []
        for _c in _tw_cookies:
            _kw = dict(
                name=_c["name"], value=_c["value"], domain=_c["domain"],
                path=_c.get("path", "/"), secure=_c.get("secure", True),
                http_only=_c.get("httpOnly", False),
            )
            _ss = _c.get("sameSite")
            if _ss and _ss in _ss_map:
                _kw["same_site"] = _ss_map[_ss]
            _params.append(cdp_network.CookieParam(**_kw))
        await page.send(cdp_network.set_cookies(_params))
        print(f"    {len(_params)} cookies injected")

    page = await browser.get("https://x.com/home")
    await asyncio.sleep(5)
    url = await page.evaluate("window.location.href")
    if "login" in url:
        print("    NOT LOGGED IN - run tw_login.py first")
        browser.stop()
        return

    print("    Logged in!")

    # Extended session warmup: browse feed, like 1-2 tweets
    print("    Warming up session (browsing timeline)...")
    await session_warmup(page)
    await browse_feed(page, random.uniform(20, 40))
    if random.random() < 0.5:
        liked = await like_random_tweet(page)
        if liked:
            print("    Liked a tweet during warmup")

    # Step 4: Run sessions
    total_posted = 0
    total_failed = 0
    session_start_time = time.time()

    for s in range(actual_sessions):
        start_idx = s * actual_batch
        end_idx = min(start_idx + actual_batch, len(reply_plan))

        if start_idx >= len(reply_plan):
            print(f"\n    No more replies to post.")
            break

        batch = reply_plan[start_idx:end_idx]

        posted, failed = await run_session(
            browser, page, batch, s + 1, actual_sessions
        )
        total_posted += posted
        total_failed += failed

        # Session break (unless this is the last session)
        if s < actual_sessions - 1 and start_idx + actual_batch < len(reply_plan):
            actual_break = session_breaks[s] if s < len(session_breaks) else break_min + random.uniform(-2, 5)
            elapsed = (time.time() - session_start_time) / 3600
            remaining_replies = len(reply_plan) - (end_idx)
            print(f"\n    SESSION {s+1} COMPLETE: {posted} posted, {failed} failed")
            print(f"    Total progress: {total_posted}/{len(reply_plan)} ({elapsed:.1f}h elapsed)")
            print(f"    Remaining: {remaining_replies} replies in {actual_sessions - s - 1} sessions")
            if actual_break > 30:
                # Long break: brief warmup browse, then idle sleep, then another warmup
                warmup = min(WARMUP_BROWSE_MIN, actual_break * 0.1)
                idle = actual_break - warmup * 2
                print(f"\n    BREAK: {actual_break:.0f} min ({actual_break/60:.1f}h) until session {s+2}")
                print(f"    -> {warmup:.0f} min browse | {idle:.0f} min idle | {warmup:.0f} min warmup")
                await session_break_browse(page, warmup)
                await asyncio.sleep(idle * 60)
                await session_break_browse(page, warmup)
            else:
                print(f"\n    BREAK: {actual_break:.0f} min (browse)...")
                await session_break_browse(page, actual_break)

    # Summary
    elapsed_total = (time.time() - session_start_time) / 60
    print(f"\n{'=' * 60}")
    print(f"  RUN COMPLETE")
    print(f"  Posted:   {total_posted}")
    print(f"  Failed:   {total_failed}")
    print(f"  Total:    {total_posted + total_failed}/{len(reply_plan)}")
    print(f"  Time:     {elapsed_total:.0f} min ({elapsed_total/60:.1f}h)")
    print(f"  Velocity: {total_posted / (elapsed_total/60):.0f}/hr effective" if elapsed_total > 0 else "")
    print(f"{'=' * 60}")

    await asyncio.sleep(2)
    browser.stop()


def show_status():
    """Show reply statistics from Notion."""
    h = notion_headers()
    statuses = {"Replied": 0, "Available": 0, "Reply Failed": 0}

    has_more = True
    start_cursor = None
    total = 0
    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        r = requests.post(
            f"https://api.notion.com/v1/databases/{TWITTER_LEADS_DB}/query",
            headers=h, json=payload, timeout=15
        )
        r.raise_for_status()
        data = r.json()
        for page in data.get("results", []):
            total += 1
            status_sel = page["properties"].get("DM Status", {}).get("select")
            status = status_sel.get("name", "") if status_sel else ""
            if status == "":
                statuses["Available"] = statuses.get("Available", 0) + 1
            else:
                statuses[status] = statuses.get(status, 0) + 1
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    print(f"\n  Twitter Leads Status ({total} total)")
    print(f"  {'_' * 35}")
    for status, count in sorted(statuses.items(), key=lambda x: -x[1]):
        pct = count / total * 100 if total else 0
        print(f"  {status:<20} {count:>4} ({pct:.0f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hedge Edge Twitter Reply Bot v3")
    parser.add_argument("--action", choices=["preview", "run", "status"], default="preview")
    parser.add_argument("--limit", type=int, default=200, help="Total replies (default: 200)")
    parser.add_argument("--batch", type=int, default=50, help="Replies per session (default: 50)")
    parser.add_argument("--sessions", type=int, default=4, help="Max sessions (default: 4)")
    parser.add_argument("--break-min", type=int, default=15, help="Break minutes between sessions (default: 15)")
    parser.add_argument("--graduated", type=int, default=0, metavar="DAY",
                        help="Graduated calibration mode: specify day 1-5")
    args = parser.parse_args()

    if args.action == "status":
        show_status()
    elif args.action == "preview":
        asyncio.run(run_replies(
            limit=args.limit, batch_size=args.batch, sessions=args.sessions,
            break_min=args.break_min, dry_run=True, graduated_day=args.graduated
        ))
    elif args.action == "run":
        asyncio.run(run_replies(
            limit=args.limit, batch_size=args.batch, sessions=args.sessions,
            break_min=args.break_min, dry_run=False, graduated_day=args.graduated
        ))