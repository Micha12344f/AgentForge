#!/usr/bin/env python3
"""
Hedge Edge - Twitter Search & Reply Bot
=========================================
Searches Twitter for queries, replies to matching tweets inline,
then saves each reply to the Notion Twitter Leads DB.

This is the unified pipeline:
  Search → Scroll results → Filter → Generate reply → Post reply → Save to Notion

Unlike tw_reply_v2.py (which reads leads FROM Notion), this bot:
  1. Searches Twitter directly for queries (hedging + pain point keywords)
  2. Scrolls search results and picks relevant tweets
  3. Generates a contextual reply via Groq LLM
  4. Posts the reply inline from the search results page
  5. Saves the handle, tweet, reply, and query to Notion

Usage:
  python scripts/tw_search_reply.py --action preview            # Preview search + replies
  python scripts/tw_search_reply.py --action run                # Search, reply, save
  python scripts/tw_search_reply.py --action run --limit 30     # Cap at 30 replies
  python scripts/tw_search_reply.py --action run --queries 10   # Use 10 queries
  python scripts/tw_search_reply.py --action status             # Show stats
"""

import asyncio, contextlib, json, os, sys, argparse, time, random, re, requests
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

import nodriver as uc
from nodriver.cdp import input_ as cdp_input

# Import humanization layer
from tw_humanize import (
    human_delay, reply_interval, typing_speed, reading_pause,
    jitter_coords, bezier_points, human_type, human_mouse_move,
    simulate_reading, session_warmup, add_natural_noise,
    ReplySession, HOURLY_SOFT_LIMIT, check_velocity,
    between_reply_actions, browse_feed, like_random_tweet,
)

# Import query generator
try:
    from tw_query_generator import generate_queries as _generate_queries
    HAS_QUERY_GEN = True
except ImportError:
    HAS_QUERY_GEN = False

# ============================================================
#  Config
# ============================================================

TWITTER_LEADS_DB = "310652ea-6c6d-81de-8a89-e65f52bfa97a"
PROFILE_DIR = os.environ.get("CHROME_PROFILE_DIR") or os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "HedgeEdge_Twitter_Profile")
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tw_search_reply_progress.json")

DAILY_REPLY_LIMIT = 50      # Conservative default
REPLIES_PER_SEARCH = 3      # Max replies per query (look organic)
MAX_SCROLLS_PER_SEARCH = 5  # How far to scroll search results
MIN_REPLY_INTERVAL = 90     # Seconds minimum between replies
HEARTBEAT_INTERVAL = 60     # Seconds between liveness log lines

# Search queries - two categories
HEDGING_QUERIES = [
    "prop firm hedging",
    "prop firm hedge account",
    "hedge prop firm challenge",
    "FTMO hedging strategy",
    "prop firm reverse trade",
    "copy trade hedge prop",
    "prop firm capital protection",
    "funded account hedging",
    "prop firm challenge hack",
    "personal broker hedge prop",
]

PAIN_POINT_QUERIES = [
    "blew my prop firm",
    "blew my funded account",
    "blown prop firm account",
    "failed prop firm challenge",
    "failed my challenge",
    "lost my funded account",
    "prop firm drawdown",
    "blown funded account",
    "prop firm challenge failed",
    "keep failing prop firm",
    "starting over prop firm",
    "prop firm so frustrating",
    "prop firm blew up",
    "lost my FTMO",
    "FTMO failed",
    "blown up today prop",
]

# Handles to never reply to (brands, competitors, ourselves)
EXCLUDED_HANDLES = {
    "andreeatrade", "breakouthunter", "dhruvtradesfx", "funded_trading",
    "itradepropfirm", "propfirmmedia", "propfirmshunter", "tradergalt",
    "hedgedge", "hedge_edge", "a87329430",
}

# Reply safety - block these patterns from ever being posted
BLOCKED_PATTERNS = [
    "hedgedge", "hedge edge", "hedg edge",
    "http", "https", "www.",
    "check out", "check this", "try this",
    "dm me", "dm for", "message me",
    "link in bio", "link in my",
    "sign up", "signup", "subscribe",
    "#", "@hedg",
]

# ============================================================
#  Progress tracking (local JSON)
# ============================================================

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "replied_tweet_urls": [],
        "replied_handles": [],
        "runs": [],
        "today_count": 0,
        "today_date": "",
    }


def save_progress(data):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def reset_daily_count(progress):
    today = date.today().isoformat()
    if progress.get("today_date") != today:
        progress["today_count"] = 0
        progress["today_date"] = today
    return progress


def _format_runtime(seconds):
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def update_heartbeat_state(state, phase, **extra):
    state["phase"] = phase
    state["phase_since"] = time.time()
    state.update(extra)


async def heartbeat_logger(state, started_at, interval=HEARTBEAT_INTERVAL):
    while not state.get("stop"):
        await asyncio.sleep(interval)
        if state.get("stop"):
            break

        query_total = state.get("query_total", 0)
        query_index = state.get("query_index", 0)
        reply_index = state.get("reply_index")
        reply_total = state.get("reply_total")
        current_handle = state.get("handle")
        query = state.get("query") or "-"
        phase_runtime = _format_runtime(time.time() - state.get("phase_since", started_at))
        uptime = _format_runtime(time.time() - started_at)

        position = f"q {query_index}/{query_total}"
        if reply_index and reply_total:
            position += f" | reply {reply_index}/{reply_total}"

        details = [
            f"uptime {uptime}",
            f"phase {state.get('phase', 'unknown')} ({phase_runtime})",
            position,
            f"posted {state.get('posted', 0)}",
            f"failed {state.get('failed', 0)}",
            f"saved {state.get('saved', 0)}",
            f"query \"{query[:60]}\"",
        ]
        if current_handle:
            details.append(f"handle @{current_handle}")

        print(f"  HEARTBEAT: {' | '.join(details)}")


# ============================================================
#  Search queries
# ============================================================

def get_search_queries(max_queries=20):
    """Get search queries - LLM-generated if available, else static."""
    if HAS_QUERY_GEN:
        try:
            queries = _generate_queries(
                n_llm=15, include_baseline=True, max_total=max_queries, shuffle=True
            )
            if queries:
                return queries[:max_queries]
        except Exception as e:
            print(f"  [!] Query generator failed: {e}, using static list")

    combined = HEDGING_QUERIES + PAIN_POINT_QUERIES
    random.shuffle(combined)
    return combined[:max_queries]


def categorize_query(query):
    """Determine if a query is hedging-related or pain-point."""
    pain_keywords = [
        "blew", "blown", "failed", "lost", "drawdown",
        "frustrat", "starting over", "blew up",
    ]
    q_lower = query.lower()
    for kw in pain_keywords:
        if kw in q_lower:
            return "Pain Point"
    return "Seeker"


# ============================================================
#  Notion helpers
# ============================================================

def notion_headers():
    return {
        "Authorization": f"Bearer {os.getenv('NOTION_API_KEY')}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def check_handle_exists(handle):
    """Check if a handle already exists in the Notion Twitter Leads DB."""
    h = notion_headers()
    payload = {
        "filter": {
            "property": "Handle",
            "title": {"equals": handle},
        },
        "page_size": 1,
    }
    try:
        r = requests.post(
            f"https://api.notion.com/v1/databases/{TWITTER_LEADS_DB}/query",
            headers=h, json=payload, timeout=15,
        )
        r.raise_for_status()
        return len(r.json().get("results", [])) > 0
    except Exception:
        return False


def save_reply_to_notion(handle, tweet_text, tweet_url, reply_text, query, category):
    """Save a completed reply to the Notion Twitter Leads DB."""
    h = notion_headers()
    today = date.today().isoformat()

    properties = {
        "Handle": {"title": [{"text": {"content": handle[:100]}}]},
        "Tweet Text": {"rich_text": [{"text": {"content": tweet_text[:2000]}}]},
        "Tweet URL": {"url": tweet_url if tweet_url else None},
        "Search Query": {"select": {"name": query[:100]}},
        "Priority": {"select": {"name": "High" if category == "Pain Point" else "Medium"}},
        "DM Status": {"select": {"name": "Replied"}},
        "DM Date": {"date": {"start": today}},
        "Notes": {"rich_text": [{"text": {"content": f"[{category}] REPLIED: {reply_text}"[:2000]}}]},
    }

    try:
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers=h,
            json={"parent": {"database_id": TWITTER_LEADS_DB}, "properties": properties},
            timeout=15,
        )
        if r.status_code in (200, 201):
            return True
        print(f"    Notion save error {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"    Notion save exception: {e}")
        return False


# ============================================================
#  LLM reply generation
# ============================================================

def generate_reply(handle, tweet_text, category):
    """Generate a contextual reply using Groq LLM."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    base_rules = """RULES (strict):
- Max 200 characters
- Sound like a real trader, casual lowercase
- NO hashtags, NO links, NO emojis
- NO product names, company names, or calls to action
- NO "check out", "DM me", "link in bio"
- Single reply, no line breaks
- Be genuine and conversational"""

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

    if category == "Pain Point":
        approach = random.choice(pain_approaches)
        prompt = f"""{base_rules}

You are a prop firm trader who has been through the same pain of failing challenges.
Reply to this tweet empathetically. {approach}.
Sound like youve been there and found a workaround.

Tweet by @{handle}: "{tweet_text[:500]}"

Reply:"""
    else:
        approach = random.choice(seeker_approaches)
        prompt = f"""{base_rules}

This trader is looking for hedging solutions. You do this already.
Reply with a direct but casual answer. {approach}.
Be helpful, not salesy.

Tweet by @{handle}: "{tweet_text[:500]}"

Reply:"""

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.75,
            max_tokens=100,
        )
        reply = resp.choices[0].message.content.strip().strip('"').strip("'")

        # Safety filter
        reply_lower = reply.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern in reply_lower:
                print(f"    BLOCKED: Reply contained '{pattern}' - regenerating")
                resp2 = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.65,
                    max_tokens=100,
                )
                reply = resp2.choices[0].message.content.strip().strip('"').strip("'")
                reply_lower = reply.lower()
                # If still blocked, skip
                for p2 in BLOCKED_PATTERNS:
                    if p2 in reply_lower:
                        print(f"    BLOCKED again: '{p2}' - skipping")
                        return None
                break

        # Add natural variation
        reply = add_natural_noise(reply)

        # Enforce length
        if len(reply) > 240:
            reply = reply[:237] + "..."

        return reply

    except Exception as e:
        print(f"    Groq error: {e}")
        return None


# ============================================================
#  Browser helpers
# ============================================================

async def wait_for(page, js_expr, timeout=30, poll=0.5):
    for _ in range(int(timeout / poll)):
        result = await page.evaluate(js_expr)
        if result:
            return result
        await page.sleep(poll)
    return None


async def ensure_logged_in(browser):
    """Navigate to home and verify we're logged in. Inject cookies if available."""
    # Cookie injection: if COOKIE_FILE is set, inject cookies via CDP
    cookie_file = os.environ.get("COOKIE_FILE")
    if cookie_file and os.path.exists(cookie_file):
        from nodriver.cdp import network as cdp_network
        print("  Injecting cookies from", cookie_file)
        with open(cookie_file, encoding="utf-8") as _cf:
            _raw = json.load(_cf)
        _targets = ["x.com", "twitter.com"]
        _tw_cookies = [c for c in _raw if any(d in c.get("domain", "") for d in _targets)]
        _ss_map = {
            "Strict": cdp_network.CookieSameSite.STRICT,
            "Lax": cdp_network.CookieSameSite.LAX,
            "None": cdp_network.CookieSameSite.NONE,
        }
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
        print(f"  {len(_params)} cookies injected")

    page = await browser.get("https://x.com/home")
    await page.sleep(5)
    url = await page.evaluate("window.location.href")
    if "home" in url and "login" not in url:
        print("  [+] Logged in (saved session)")
        return page
    print("  [!] NOT logged in - run tw_login.py first")
    return None


# ============================================================
#  Search results extraction
# ============================================================

async def search_and_extract(page, query, max_scrolls=5):
    """Search Twitter for a query and extract tweets from results."""
    encoded = query.replace(" ", "+")
    url = f"https://x.com/search?q={encoded}&src=typed_query&f=live"
    page = await page._browser.get(url)

    has_tweets = await wait_for(
        page,
        'document.querySelectorAll(\'[data-testid="tweet"]\').length > 0 ? "yes" : ""',
        timeout=20,
    )
    if not has_tweets:
        return page, []

    all_tweets = []
    seen_urls = set()

    for scroll_i in range(max_scrolls):
        tw_json = await page.evaluate("""
            JSON.stringify(Array.from(document.querySelectorAll('[data-testid="tweet"]')).map(t => {
                const userEl = t.querySelector('[data-testid="User-Name"]');
                const textEl = t.querySelector('[data-testid="tweetText"]');
                const timeEl = t.querySelector('time');
                const linkEl = t.querySelector('a[href*="/status/"]');
                const handle = userEl
                    ? (userEl.querySelector('a[href^="/"]')?.href || '').split('/').pop()
                    : '';
                const displayName = userEl ? userEl.innerText.split('\\n')[0] : '';

                // Get bounding rect for inline reply targeting
                const rect = t.getBoundingClientRect();

                return {
                    handle: handle || '',
                    display_name: displayName || '',
                    text: textEl?.innerText || '',
                    time: timeEl?.getAttribute('datetime') || '',
                    url: linkEl?.href || '',
                    top: Math.round(rect.top),
                    bottom: Math.round(rect.bottom),
                };
            }))
        """)
        tweets = json.loads(tw_json) if tw_json else []

        for t in tweets:
            if t["url"] and t["url"] not in seen_urls:
                seen_urls.add(t["url"])
                t["query"] = query
                all_tweets.append(t)

        # Organic scrolling between pages of results
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(random.uniform(1.5, 3.5))

    return page, all_tweets


# ============================================================
#  Inline reply posting (from tweet detail page)
# ============================================================

async def post_reply_to_tweet(page, tweet_url, reply_text):
    """Navigate to a tweet and post a reply with full humanization.

    Flow:
      1. Go to tweet URL
      2. Wait for page load
      3. Simulate reading the tweet
      4. Click reply box, type reply with human timing
      5. Click Reply/Post button
      6. Verify submission
    """
    # 1. Navigate to the tweet
    page = await page._browser.get(tweet_url)
    await asyncio.sleep(random.uniform(3.0, 5.0))

    # 2. Wait for tweet to render
    loaded = await wait_for(
        page,
        'document.querySelector(\'[data-testid="tweetText"]\') ? "yes" : ""',
        timeout=20,
    )
    if not loaded:
        return page, False, "Tweet page did not load"

    # 3. Simulate reading
    tweet_visible = await page.evaluate("""
        (function() {
            const el = document.querySelector('[data-testid="tweetText"]');
            return el ? el.textContent : "";
        })()
    """) or ""
    await simulate_reading(page, tweet_visible)

    # 4. Find and click reply box
    reply_box_pos = await page.evaluate("""
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
    """)

    if not reply_box_pos:
        return page, False, "Could not find reply box"

    coords = json.loads(reply_box_pos)
    await human_mouse_move(page, coords["x"], coords["y"])
    await asyncio.sleep(human_delay(0.3, 0.8))

    # Focus
    await page.evaluate("""
        (function() {
            const box = document.querySelector('[data-testid="tweetTextarea_0"]');
            if (box) { box.click(); box.focus(); return; }
            const inputs = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
            if (inputs.length > 0) { inputs[0].click(); inputs[0].focus(); }
        })()
    """)
    await asyncio.sleep(human_delay(0.5, 1.2))

    # 5. Type the reply
    await human_type(page, reply_text)
    await asyncio.sleep(human_delay(0.3, 0.6))

    # Verify text entered
    typed = await page.evaluate("""
        (function() {
            const boxes = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
            for (const b of boxes) { if (b.textContent.length > 0) return b.textContent.length; }
            return 0;
        })()
    """)
    if not typed:
        return page, False, "Reply text was not entered"

    # Brief pause to re-read
    await asyncio.sleep(human_delay(0.8, 2.5))

    # 6. Find and click Reply/Post button
    btn_pos = await page.evaluate("""
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
    """)

    if not btn_pos:
        return page, False, "Could not find Reply/Post button"

    btn_coords = json.loads(btn_pos)
    await human_mouse_move(
        page, btn_coords["x"], btn_coords["y"],
        start_x=coords["x"] + random.randint(-20, 20),
        start_y=coords["y"] + random.randint(-10, 10),
    )

    await asyncio.sleep(random.uniform(3.0, 5.0))

    # 7. Verify submission
    textbox_len = await page.evaluate("""
        (function() {
            const boxes = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
            for (const b of boxes) { if (b.textContent.length > 0) return b.textContent.length; }
            return 0;
        })()
    """)

    if textbox_len and textbox_len > 5:
        # Retry click
        await human_mouse_move(
            page, btn_coords["x"], btn_coords["y"],
            start_x=btn_coords["x"] + random.randint(-30, 30),
            start_y=btn_coords["y"] + random.randint(-20, 20),
        )
        await asyncio.sleep(random.uniform(3.0, 5.0))
        textbox_len2 = await page.evaluate("""
            (function() {
                const boxes = document.querySelectorAll('[role="textbox"][contenteditable="true"]');
                for (const b of boxes) { if (b.textContent.length > 0) return b.textContent.length; }
                return 0;
            })()
        """)
        if textbox_len2 and textbox_len2 > 5:
            return page, False, f"Reply button click failed - textbox still has {textbox_len2} chars"

    # Check for Twitter errors
    body_text = await page.evaluate('document.body?.innerText?.substring(0, 1000) || ""')
    error_phrases = ["error", "try again", "something went wrong", "rate limit", "unable to"]
    for phrase in error_phrases:
        if phrase in body_text.lower():
            return page, False, f"Twitter error: '{phrase}'"

    # Check for our reply on the page
    reply_snippet = reply_text[:40].replace("'", "").replace('"', "")
    found_reply = await page.evaluate(
        "(function() {"
        '  const tweets = document.querySelectorAll(\'[data-testid="tweetText"]\');'
        "  for (const t of tweets) {"
        '    if (t.textContent.includes("' + reply_snippet + '")) return true;'
        "  }"
        "  return false;"
        "})()"
    )

    if found_reply:
        return page, True, "Reply posted and verified on page"

    if not textbox_len or textbox_len == 0:
        return page, True, "Reply likely posted (textbox cleared)"

    return page, False, "Reply could not be verified"


# ============================================================
#  Main pipeline: Search → Filter → Reply → Save to Notion
# ============================================================

async def run_search_reply_pipeline(
    limit=50,
    max_queries=15,
    replies_per_query=3,
    dry_run=False,
):
    """Full pipeline: search Twitter, reply to relevant tweets, save to Notion.

    For each query:
      1. Search Twitter for the query
      2. Scroll results, extract tweets
      3. Filter: skip already-replied, excluded handles, irrelevant
      4. Generate replies via Groq LLM
      5. Navigate to each tweet, post reply with humanization
      6. Save reply + tweet to Notion
      7. Organic browsing between replies
    """
    now = datetime.now(timezone.utc)
    progress = load_progress()
    progress = reset_daily_count(progress)

    queries = get_search_queries(max_queries)
    query_mode = "LLM+baseline" if HAS_QUERY_GEN else "static"

    print("=" * 60)
    mode_label = "[PREVIEW]" if dry_run else "[LIVE]"
    print(f"  Hedge Edge Twitter Search & Reply Bot {mode_label}")
    print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Target: {limit} replies | {len(queries)} queries ({query_mode})")
    print(f"  Replies per query: {replies_per_query} | Today so far: {progress['today_count']}")
    print("=" * 60)

    if dry_run:
        # Preview mode: just search and show what we'd reply to
        print(f"\n[1] Searching Twitter (preview only)...\n")
        browser = await uc.start(
            headless=False,
            user_data_dir=PROFILE_DIR,
            browser_args=[
                "--window-size=1280,720",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-software-rasterizer",
            ],
        )
        page = await ensure_logged_in(browser)
        if not page:
            browser.stop()
            return

        total_found = 0
        total_eligible = 0
        for qi, query in enumerate(queries):
            print(f"  [{qi+1}/{len(queries)}] \"{query}\"")
            page, tweets = await search_and_extract(page, query, max_scrolls=3)
            print(f"    Found {len(tweets)} tweets")

            eligible = 0
            for t in tweets:
                handle = t["handle"].lower().lstrip("@")
                if not handle or handle in EXCLUDED_HANDLES:
                    continue
                if t["url"] in progress.get("replied_tweet_urls", []):
                    continue
                eligible += 1
                if eligible <= replies_per_query:
                    cat = categorize_query(query)
                    reply = generate_reply(handle, t["text"], cat)
                    if reply:
                        print(f"    @{handle:<20} -> {reply[:70]}...")
                    else:
                        print(f"    @{handle:<20} -> [no reply generated]")

            total_found += len(tweets)
            total_eligible += eligible
            await asyncio.sleep(random.uniform(2, 4))

        browser.stop()
        print(f"\n  PREVIEW COMPLETE: {total_found} tweets found, {total_eligible} eligible")
        print(f"  Use --action run to post replies.")
        return

    # ---- LIVE MODE ----
    print(f"\n[1] Launching browser...")
    browser = await uc.start(
        headless=False,
        user_data_dir=PROFILE_DIR,
        browser_args=[
            "--window-size=1280,720",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-software-rasterizer",
        ],
    )

    page = await ensure_logged_in(browser)
    if not page:
        browser.stop()
        return

    # Warmup: browse feed casually to establish organic session fingerprint
    print("  Warming up session...")
    try:
        await session_warmup(page)
        await browse_feed(page, random.uniform(15, 30))
        print("  Warmup complete.")
    except Exception as warmup_err:
        print(f"  Warmup failed ({warmup_err}), continuing anyway...")

    session = ReplySession(daily_limit=limit)
    total_posted = 0
    total_failed = 0
    total_skipped = 0
    total_saved = 0
    run_start = time.time()
    heartbeat_state = {
        "stop": False,
        "phase": "initializing",
        "phase_since": time.time(),
        "query_total": len(queries),
        "query_index": 0,
        "reply_index": None,
        "reply_total": None,
        "query": None,
        "handle": None,
        "posted": 0,
        "failed": 0,
        "saved": 0,
    }
    heartbeat_task = asyncio.create_task(heartbeat_logger(heartbeat_state, run_start))

    run_log = {
        "timestamp": now.isoformat(),
        "queries_used": len(queries),
        "replies": [],
    }

    print(f"\n[2] Starting search & reply loop...\n")
    print(f"  Heartbeat logging enabled ({HEARTBEAT_INTERVAL}s interval)")

    try:
        for qi, query in enumerate(queries):
            if total_posted >= limit:
                print(f"\n  Reached reply limit ({limit})")
                break

            if not session.can_reply():
                print(f"\n  Session safety limit reached")
                break

            category = categorize_query(query)
            update_heartbeat_state(
                heartbeat_state,
                "searching",
                query_index=qi + 1,
                reply_index=None,
                reply_total=None,
                query=query,
                handle=None,
            )
            print(f"\n  [{qi+1}/{len(queries)}] Searching: \"{query}\" [{category}]")

            # Search
            page, tweets = await search_and_extract(page, query, max_scrolls=MAX_SCROLLS_PER_SEARCH)
            print(f"    Found {len(tweets)} tweets")

            if not tweets:
                continue

            # Filter eligible tweets
            eligible = []
            for t in tweets:
                handle = t["handle"].lower().lstrip("@")
                if not handle:
                    continue
                if handle in EXCLUDED_HANDLES:
                    continue
                if t["url"] in progress.get("replied_tweet_urls", []):
                    continue
                if handle in progress.get("replied_handles", []):
                    continue
                if not t["text"].strip():
                    continue
                eligible.append(t)

            if not eligible:
                print(f"    No eligible tweets (all filtered)")
                total_skipped += len(tweets)
                continue

            # Shuffle so we don't always reply to the top result
            random.shuffle(eligible)
            batch = eligible[:replies_per_query]
            update_heartbeat_state(heartbeat_state, "processing batch", reply_total=len(batch))
            print(f"    Eligible: {len(eligible)} | Replying to: {len(batch)}")

            for ti, tweet in enumerate(batch):
                if total_posted >= limit or not session.can_reply():
                    break

                handle = tweet["handle"].lower().lstrip("@")
                tweet_url = tweet["url"]
                tweet_text = tweet["text"][:500]

                update_heartbeat_state(
                    heartbeat_state,
                    "preparing reply",
                    reply_index=ti + 1,
                    reply_total=len(batch),
                    handle=handle,
                )
                print(f"\n    [{ti+1}/{len(batch)}] @{handle}")
                print(f"      Tweet: {tweet_text[:80]}...")

                # Check if already in Notion (dedup)
                if check_handle_exists(handle):
                    print(f"      SKIP: already in Notion")
                    total_skipped += 1
                    continue

                # Generate reply
                reply = generate_reply(handle, tweet_text, category)
                if not reply:
                    print(f"      SKIP: no reply generated")
                    total_skipped += 1
                    continue

                print(f"      Reply: {reply[:80]}...")

                # Post the reply
                update_heartbeat_state(heartbeat_state, "posting reply")
                page, success, msg = await post_reply_to_tweet(page, tweet_url, reply)

                if success:
                    print(f"      POSTED: {msg}")
                    total_posted += 1
                    heartbeat_state["posted"] = total_posted
                    session.record_reply()

                    # Save to Notion
                    update_heartbeat_state(heartbeat_state, "saving to notion")
                    saved = save_reply_to_notion(
                        handle=handle,
                        tweet_text=tweet_text,
                        tweet_url=tweet_url,
                        reply_text=reply,
                        query=query,
                        category=category,
                    )
                    if saved:
                        total_saved += 1
                        heartbeat_state["saved"] = total_saved
                        print(f"      Notion: saved")
                    else:
                        print(f"      Notion: FAILED to save")

                    # Update local progress
                    progress["replied_tweet_urls"].append(tweet_url)
                    progress["replied_handles"].append(handle)
                    progress["today_count"] += 1
                    save_progress(progress)

                    run_log["replies"].append({
                        "handle": handle,
                        "tweet_url": tweet_url,
                        "reply": reply,
                        "query": query,
                        "category": category,
                        "notion_saved": saved,
                    })
                else:
                    print(f"      FAILED: {msg}")
                    total_failed += 1
                    heartbeat_state["failed"] = total_failed
                    session.record_error()

                # Organic behavior between replies
                if ti < len(batch) - 1 or qi < len(queries) - 1:
                    update_heartbeat_state(heartbeat_state, "organic action")
                    action_desc = await between_reply_actions(page)
                    print(f"      Organic: {action_desc}")

                    delay = session.next_delay()
                    delay = max(delay, MIN_REPLY_INTERVAL)
                    update_heartbeat_state(heartbeat_state, f"cooldown {delay:.0f}s")
                    print(f"      Next in {delay:.0f}s ({delay/60:.1f} min)...")
                    await asyncio.sleep(delay)

            # Brief organic pause between queries
            if qi < len(queries) - 1 and total_posted < limit:
                browse_time = random.uniform(10, 30)
                update_heartbeat_state(heartbeat_state, f"between-query browse {browse_time:.0f}s")
                print(f"\n    -- Between-query browse ({browse_time:.0f}s) --")
                await browse_feed(page, browse_time)
    finally:
        heartbeat_state["stop"] = True
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task

    # Save run stats
    elapsed = (time.time() - run_start) / 60
    run_log["posted"] = total_posted
    run_log["failed"] = total_failed
    run_log["skipped"] = total_skipped
    run_log["saved_to_notion"] = total_saved
    run_log["elapsed_min"] = round(elapsed, 1)
    progress["runs"].append(run_log)
    save_progress(progress)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  RUN COMPLETE")
    print(f"  Posted:     {total_posted}")
    print(f"  Failed:     {total_failed}")
    print(f"  Skipped:    {total_skipped}")
    print(f"  Notion:     {total_saved} saved")
    print(f"  Time:       {elapsed:.0f} min ({elapsed/60:.1f}h)")
    if elapsed > 0:
        print(f"  Velocity:   {total_posted / (elapsed / 60):.0f}/hr")
    print(f"  Today total: {progress['today_count']}")
    print(f"{'=' * 60}")

    await asyncio.sleep(2)
    browser.stop()


# ============================================================
#  Status command
# ============================================================

def show_status():
    """Show reply statistics from progress file and Notion."""
    progress = load_progress()
    print(f"\n  Local Progress")
    print(f"  {'_' * 35}")
    print(f"  Today ({progress.get('today_date', '?')}): {progress.get('today_count', 0)} replies")
    print(f"  Total replied handles: {len(progress.get('replied_handles', []))}")
    print(f"  Total replied tweets:  {len(progress.get('replied_tweet_urls', []))}")
    print(f"  Runs: {len(progress.get('runs', []))}")

    if progress.get("runs"):
        last = progress["runs"][-1]
        print(f"\n  Last Run: {last.get('timestamp', '?')}")
        print(f"    Posted: {last.get('posted', 0)} | Failed: {last.get('failed', 0)}")
        print(f"    Saved to Notion: {last.get('saved_to_notion', 0)}")
        print(f"    Elapsed: {last.get('elapsed_min', 0)} min")

    # Notion stats
    h = notion_headers()
    try:
        statuses = {}
        has_more = True
        start_cursor = None
        total = 0
        while has_more:
            payload = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            r = requests.post(
                f"https://api.notion.com/v1/databases/{TWITTER_LEADS_DB}/query",
                headers=h, json=payload, timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            for pg in data.get("results", []):
                total += 1
                sel = pg["properties"].get("DM Status", {}).get("select")
                st = sel.get("name", "") if sel else ""
                statuses[st or "Available"] = statuses.get(st or "Available", 0) + 1
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        print(f"\n  Notion Twitter Leads ({total} total)")
        print(f"  {'_' * 35}")
        for status, count in sorted(statuses.items(), key=lambda x: -x[1]):
            pct = count / total * 100 if total else 0
            print(f"  {status:<20} {count:>4} ({pct:.0f}%)")
    except Exception as e:
        print(f"\n  Notion query failed: {e}")


# ============================================================
#  CLI entry point
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hedge Edge Twitter Search & Reply Bot")
    parser.add_argument("--action", choices=["preview", "run", "status"], default="preview")
    parser.add_argument("--limit", type=int, default=50, help="Max replies per run (default: 50)")
    parser.add_argument("--queries", type=int, default=15, help="Number of search queries (default: 15)")
    parser.add_argument("--per-query", type=int, default=3, help="Max replies per query (default: 3)")
    args = parser.parse_args()

    if args.action == "status":
        show_status()
    elif args.action in ("preview", "run"):
        try:
            asyncio.run(
                run_search_reply_pipeline(
                    limit=args.limit,
                    max_queries=args.queries,
                    replies_per_query=args.per_query,
                    dry_run=(args.action == "preview"),
                )
            )
        except KeyboardInterrupt:
            print("\n  Interrupted by user.")
        except Exception as exc:
            import traceback
            print(f"\n  FATAL: {exc}")
            traceback.print_exc()
            import sys
            sys.exit(1)
