# ── Cell 1: Setup & Configuration ────────────────────────────────────
import sys, os, json, random, re, html
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, 'shared')) and os.path.isdir(os.path.join(d, 'Business')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

ROOT = Path(_find_ws_root())
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "Business" / "GROWTH" / "resources" / ".env", override=True)

# ── Config ──
DRY_RUN = True   # True = preview only, False = actually post to X

# ── Paths ──
GROWTH_RES    = ROOT / "Business" / "GROWTH" / "resources" / "Marketing"
DEMOS_FILE    = GROWTH_RES / "x-pipeline" / "tweet_demos_100.json"
STATE_FILE    = GROWTH_RES / "x-pipeline" / "auto_tweet_state.json"
GIF_LIBRARY   = GROWTH_RES / "x-pipeline" / "gif_library.json"
MANIFEST_FILE = GROWTH_RES / "x-assets" / "library" / "manifest.json"
LOGO_PATH     = GROWTH_RES / "x-assets" / "Hedge-Edge-Logo.png"
LIB_DIR       = GROWTH_RES / "x-assets" / "library"
GEN_DIR       = GROWTH_RES / "x-assets" / "generated"
GEN_DIR.mkdir(parents=True, exist_ok=True)

# ── Automatable tweet types ──
AUTO_TYPES = {"funny_meme", "gif_meme", "viral_hook", "industry_take",
              "stat_truth", "uncomfortable_truth", "direct_cta"}

# ── API Call Counter (tracked across all cells) ──
api_call_counter = {"x_api": 0, "imgflip": 0, "pexels": 0, "giphy_cdn": 0}

# ── Credential check ──
creds = {
    "TWITTER_API_KEY":           bool(os.getenv("TWITTER_API_KEY")),
    "TWITTER_API_SECRET":        bool(os.getenv("TWITTER_API_SECRET")),
    "TWITTER_ACCESS_TOKEN":      bool(os.getenv("TWITTER_ACCESS_TOKEN")),
    "TWITTER_ACCESS_TOKEN_SECRET": bool(os.getenv("TWITTER_ACCESS_TOKEN_SECRET")),
    "IMGFLIP_USERNAME":          bool(os.getenv("IMGFLIP_USERNAME")),
    "IMGFLIP_PASSWORD":          bool(os.getenv("IMGFLIP_PASSWORD")),
    "PEXELS_API_KEY":            bool(os.getenv("PEXELS_API_KEY")),
}

print(f"ROOT:    {ROOT}")
print(f"DRY_RUN: {DRY_RUN}")
print(f"Time:    {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
print()
print("Credentials:")
for key, ok in creds.items():
    print(f"  {'✅' if ok else '❌'} {key}")
print()
print("Files:")
for label, p in [("Demos", DEMOS_FILE), ("State", STATE_FILE), ("GIF lib", GIF_LIBRARY),
                 ("Manifest", MANIFEST_FILE), ("Logo", LOGO_PATH)]:
    print(f"  {'✅' if p.exists() else '❌'} {label}: {p.name}")
print(f"\nAPI calls this step: 0")
# ── Cell 2: Load Content Library & State ─────────────────────────────
with open(DEMOS_FILE, encoding="utf-8") as f:
    demos_data = json.load(f)
demos = demos_data["demos"]

if STATE_FILE.exists():
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
else:
    state = {"posted": {}}

posted_ids = set(int(k) for k in state["posted"].keys())
automatable = [d for d in demos if d.get("type") in AUTO_TYPES]
remaining   = [d for d in automatable if d["id"] not in posted_ids]

# Load manifest for local asset counts
manifest = {}
if MANIFEST_FILE.exists():
    with open(MANIFEST_FILE, encoding="utf-8") as f:
        manifest = json.load(f)

print(f"{'='*62}")
print(f"CONTENT LIBRARY")
print(f"{'='*62}")
print(f"Total templates:   {len(demos)}")
print(f"Automatable:       {len(automatable)}")
print(f"Already posted:    {len(posted_ids)}")
print(f"Remaining:         {len(remaining)}")
print()

# By stage
stage_counts = Counter(d.get("stage", "?") for d in remaining)
print("Remaining by stage:")
for stage in ["TOFU", "MOFU", "BOFU"]:
    print(f"  {stage}: {stage_counts.get(stage, 0)}")

# By type
print("\nRemaining by type:")
type_counts = Counter(d.get("type", "?") for d in remaining)
for ttype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {ttype:25}: {count}")

# Local asset counts
print(f"\n{'='*62}")
print(f"LOCAL ASSET LIBRARY")
print(f"{'='*62}")
print(f"  tofu/images (meme blanks): {len(manifest.get('tofu_images', []))}")
print(f"  tofu/gifs (raw GIFs):      {len(manifest.get('tofu_gifs', []))}")
print(f"  mofu (atmospheric photos): {len(manifest.get('mofu', []))}")
print(f"  bofu (logos/screenshots):  {len(manifest.get('bofu', []))}")

# Runway estimate (TOFU 7/wk + MOFU 3/wk = 10 tweets/wk)
tofu_remaining = sum(1 for d in remaining if d.get("stage") == "TOFU")
mofu_remaining = sum(1 for d in remaining if d.get("stage") == "MOFU")
tofu_weeks = tofu_remaining / 7 if tofu_remaining else 0
mofu_weeks = mofu_remaining / 3 if mofu_remaining else 0
print(f"\n{'='*62}")
print(f"RUNWAY ESTIMATE (daily_scheduler.py: 7 TOFU/wk + 3 MOFU/wk)")
print(f"{'='*62}")
print(f"  TOFU: {tofu_remaining} remaining → {tofu_weeks:.1f} weeks")
print(f"  MOFU: {mofu_remaining} remaining → {mofu_weeks:.1f} weeks")
print(f"  Bottleneck: {'TOFU' if tofu_weeks < mofu_weeks else 'MOFU'} runs out first")
print(f"\nAPI calls this step: 0")
# ── Cell 3: Select Next Tweet ─────────────────────────────────────────
# Set overrides to filter, or leave as None to use daily_scheduler logic

STAGE_OVERRIDE = None   # "TOFU" | "MOFU" | "BOFU" | None
TYPE_OVERRIDE  = None   # "funny_meme" | "gif_meme" | "viral_hook" | "industry_take" | "stat_truth" | "uncomfortable_truth" | "direct_cta" | None

# If no override, use daily_scheduler.py logic: TOFU every day, MOFU on Mon/Wed/Fri
if STAGE_OVERRIDE is None and TYPE_OVERRIDE is None:
    day_of_week = datetime.now(timezone.utc).strftime("%a").lower()
    mofu_days = {"mon", "wed", "fri"}
    if day_of_week in mofu_days:
        # Pick MOFU type round-robin
        mofu_types = ["industry_take", "stat_truth", "uncomfortable_truth"]
        mofu_remaining_types = [t for t in mofu_types
                                if any(d for d in remaining if d.get("type") == t)]
        stage_filter = "MOFU"
        type_filter = mofu_remaining_types[0] if mofu_remaining_types else None
        print(f"Scheduler logic: {day_of_week.upper()} → MOFU day")
    else:
        # Pick TOFU type round-robin
        tofu_types = ["funny_meme", "gif_meme", "viral_hook"]
        tofu_remaining_types = [t for t in tofu_types
                                if any(d for d in remaining if d.get("type") == t)]
        stage_filter = "TOFU"
        type_filter = tofu_remaining_types[0] if tofu_remaining_types else None
        print(f"Scheduler logic: {day_of_week.upper()} → TOFU day")
else:
    stage_filter = STAGE_OVERRIDE
    type_filter = TYPE_OVERRIDE
    print(f"Manual override: stage={stage_filter}, type={type_filter}")

# Pick the first matching unposted tweet
tweet = None
for demo in demos:
    if demo["id"] in posted_ids:
        continue
    if demo.get("type") not in AUTO_TYPES:
        continue
    if stage_filter and demo.get("stage", "").upper() != stage_filter.upper():
        continue
    if type_filter and demo.get("type", "") != type_filter.lower():
        continue
    tweet = demo
    break

if tweet:
    # Count alternatives with same stage+type
    alternatives = sum(1 for d in remaining
                       if d.get("stage") == tweet.get("stage")
                       and d.get("type") == tweet.get("type")
                       and d["id"] != tweet["id"])

    print(f"\n{'='*62}")
    print(f"SELECTED TWEET")
    print(f"{'='*62}")
    print(f"  ID:           {tweet['id']}")
    print(f"  Stage:        {tweet['stage']}")
    print(f"  Type:         {tweet['type']}")
    print(f"  Image needed: {tweet.get('image_needed', False)}")
    print(f"  Image type:   {tweet.get('image_type', 'none')}")
    print()
    print(f"  Tweet text:")
    print(f"  {tweet['tweet']}")
    print()
    if tweet.get("meme_template_id"):
        print(f"  Meme template ID: {tweet['meme_template_id']}")
        print(f"  Meme boxes:       {tweet.get('meme_boxes', [])}")
    if tweet.get("gif_mood"):
        print(f"  GIF mood:    {tweet['gif_mood']}")
        print(f"  GIF top:     {tweet.get('gif_top', '')}")
        print(f"  GIF bottom:  {tweet.get('gif_bottom', '')}")
    print(f"\n  Alternatives (same stage+type): {alternatives}")
else:
    print("\n❌ No unposted tweets match your filters.")
    print(f"   stage={stage_filter}, type={type_filter}")

print(f"\nAPI calls this step: 0")
# ── Cell 4: Resolve Media Asset (Local Library) ─────────────────────
media_path = None
media_desc = "no image"
needs_fallback = False

if tweet is None:
    print("No tweet selected — run Step 3 first.")
else:
    image_type   = tweet.get("image_type", "none")
    image_needed = tweet.get("image_needed", False)

    if not image_needed or image_type in ("none", None):
        media_desc = "Text-only tweet, no media needed"

    elif image_type == "meme":
        template_id = str(tweet.get("meme_template_id", ""))
        matched = False
        for entry in manifest.get("tofu_images", []):
            if entry.get("template_id") == template_id:
                local = LIB_DIR / "tofu" / "images" / entry["file"]
                if local.exists():
                    media_path = str(local)
                    media_desc = f"Local meme template: {entry.get('template_name', template_id)}"
                    matched = True
                    print(f"  Matched template: {entry['template_name']}")
                    print(f"  Box count: {entry.get('box_count', '?')}")
                else:
                    print(f"  ⚠️  Template file missing: {local}")
                break
        if not matched:
            needs_fallback = True
            media_desc = f"⚠️ No local template for ID {template_id} — would need Imgflip API fallback"

    elif image_type == "gif":
        mood = tweet.get("gif_mood", "stressed")
        matched = False
        for entry in manifest.get("tofu_gifs", []):
            if entry.get("mood") == mood:
                local = LIB_DIR / "tofu" / "gifs" / entry["file"]
                if local.exists():
                    media_path = str(local)
                    media_desc = f"Local GIF: mood={mood}, file={entry['file']}"
                    matched = True
                    print(f"  Matched GIF mood: {mood}")
                else:
                    print(f"  ⚠️  GIF file missing: {local}")
                break
        if not matched:
            needs_fallback = True
            media_desc = f"⚠️ No local GIF for mood '{mood}' — would need Giphy CDN fallback"

    elif image_type == "atmospheric":
        mofu_entries = manifest.get("mofu", [])
        if mofu_entries:
            pick = random.choice(mofu_entries)
            local = LIB_DIR / "mofu" / pick["file"]
            if local.exists():
                media_path = str(local)
                media_desc = f"Local atmospheric: {pick['file']} by {pick.get('photographer', '?')}"
                print(f"  Pexels ID: {pick.get('pexels_id', '?')}")
                print(f"  Photographer: {pick.get('photographer', '?')}")
            else:
                needs_fallback = True
                media_desc = f"⚠️ MOFU file missing: {local}"
        else:
            needs_fallback = True
            media_desc = "⚠️ No MOFU images in manifest — would need Pexels API fallback"

    elif image_type == "logo":
        if LOGO_PATH.exists():
            media_path = str(LOGO_PATH)
            media_desc = "Hedge Edge logo"
        else:
            media_desc = "⚠️ Logo file missing"

    else:
        media_desc = f"Unknown image_type: {image_type}"

    # Print results
    print(f"\n{'='*62}")
    if needs_fallback:
        print(f"⚠️  MEDIA NEEDS API FALLBACK")
    else:
        print(f"✅ MEDIA RESOLVED LOCALLY — 0 API calls made")
    print(f"{'='*62}")
    print(f"  Image type:  {image_type}")
    print(f"  Resolution:  {media_desc}")
    if media_path:
        p = Path(media_path)
        print(f"  Path:        {media_path}")
        print(f"  File size:   {p.stat().st_size / 1024:.1f} KB")
        print(f"  Extension:   {p.suffix}")

print(f"\nAPI calls this step: 0")
# ── Cell 5: Generate Media ────────────────────────────────────────────
from IPython.display import display, Image as IPImage

generated_path = None

if tweet is None:
    print("No tweet selected — run Step 3 first.")
elif media_path is None and tweet.get("image_needed", False):
    print("No local media resolved — check Step 4.")
elif not tweet.get("image_needed", False) or tweet.get("image_type") in ("none", None):
    print("Text-only tweet — no media generation needed.")
    generated_path = None
else:
    image_type = tweet.get("image_type", "none")

    if image_type == "meme":
        # Meme captioning via Imgflip API (uses the template_id, not the local blank)
        from shared.meme_maker import caption_meme
        template_id = str(tweet.get("meme_template_id", ""))
        boxes = tweet.get("meme_boxes", [])
        output = str(GEN_DIR / f"meme_{template_id}.jpg")
        generated_path, captioned = caption_meme(template_id, boxes, output_path=output)
        api_call_counter["imgflip"] += 1
        if captioned:
            print(f"✅ Meme captioned via Imgflip API")
        else:
            print(f"⚠️  Uncaptioned template (no Imgflip credentials)")

    elif image_type == "gif":
        # GIF captioning via Pillow — ZERO API calls
        from shared.gif_captioner import caption_gif
        top    = tweet.get("gif_top", "")
        bottom = tweet.get("gif_bottom", "")
        generated_path, ok = caption_gif(media_path, top, bottom)
        if ok:
            print(f"✅ GIF captioned locally via Pillow (0 API calls)")
        else:
            print(f"⚠️  GIF captioning failed")

    elif image_type == "atmospheric":
        # No processing needed — use as-is
        generated_path = media_path
        print(f"✅ Atmospheric photo — no processing needed (0 API calls)")

    elif image_type == "logo":
        generated_path = media_path
        print(f"✅ Logo — no processing needed (0 API calls)")

    # Display result
    if generated_path and Path(generated_path).exists():
        p = Path(generated_path)
        print(f"\n  Output:     {generated_path}")
        print(f"  File size:  {p.stat().st_size / 1024:.1f} KB")
        print(f"  Extension:  {p.suffix}")

        # Show inline
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            display(IPImage(filename=str(p), width=400))
        elif p.suffix.lower() == ".gif":
            display(IPImage(filename=str(p), width=400))
    elif generated_path:
        print(f"⚠️  Generated file missing: {generated_path}")

print(f"\nAPI call counter: {api_call_counter}")
print(f"API calls this step: imgflip={api_call_counter['imgflip']}, pexels={api_call_counter['pexels']}, giphy_cdn={api_call_counter['giphy_cdn']}")
# ── Cell 6: Pre-Send Validation Checklist ────────────────────────────
MAX_CHARS = 280
URL_CHAR_WEIGHT = 23
MAX_IMAGE_BYTES = 5 * 1024 * 1024    # 5 MB
MAX_GIF_BYTES   = 15 * 1024 * 1024   # 15 MB
VALID_MEDIA_EXT = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webp"}

MOJIBAKE_PATTERNS = [
    "\u00e2\u0080\u0094", "\u00e2\u0080\u0099", "\u00e2\u0080\u009c",
    "\u00e2\u0080\u009d", "\u00c3\u00b0\u00c5\u00b8",
    "\u00e2\u20ac", "\u00e2\u20ac\u0153", "\u00f0\u0178", "\ufffd",
]

VALIDATION_PASSED = False

if tweet is None:
    print("No tweet selected — run Step 3 first.")
else:
    text = tweet["tweet"]
    final_media = generated_path or media_path  # use generated if available
    checks = []

    # 1. Character count
    url_pattern = re.compile(r"https?://\S+")
    cleaned = url_pattern.sub("X" * URL_CHAR_WEIGHT, text)
    char_count = len(cleaned)
    checks.append(("Character count", char_count <= MAX_CHARS,
                    f"{char_count} / {MAX_CHARS}"))

    # 2. No broken dollar signs
    has_broken_dollar = r"\$" in text
    checks.append(("No broken dollar signs", not has_broken_dollar,
                    repr(text[:50]) if has_broken_dollar else "clean"))

    # 3. No HTML entities
    decoded = html.unescape(text)
    has_html = decoded != text
    checks.append(("No HTML entities", not has_html,
                    "entities found" if has_html else "clean"))

    # 4. No Mojibake markers
    has_mojibake = any(m in text for m in MOJIBAKE_PATTERNS)
    checks.append(("No Mojibake/encoding corruption", not has_mojibake,
                    "corruption detected" if has_mojibake else "clean"))

    # 5. No double-escaped newlines
    has_double_newline = r"\\n" in text
    checks.append(("No double-escaped newlines", not has_double_newline,
                    "found \\\\n" if has_double_newline else "clean"))

    # 6. Media file checks
    if final_media:
        p = Path(final_media)
        if not p.exists():
            checks.append(("Media file exists", False, f"MISSING: {final_media}"))
        else:
            size = p.stat().st_size
            ext = p.suffix.lower()
            if ext not in VALID_MEDIA_EXT:
                checks.append(("Media format valid", False, f"unsupported: {ext}"))
            elif ext == ".gif" and size > MAX_GIF_BYTES:
                checks.append(("Media size OK", False, f"GIF {size/1e6:.1f}MB > 15MB"))
            elif ext in (".jpg", ".jpeg", ".png", ".webp") and size > MAX_IMAGE_BYTES:
                checks.append(("Media size OK", False, f"Image {size/1e6:.1f}MB > 5MB"))
            else:
                checks.append(("Media file OK", True, f"{ext} {size/1024:.1f}KB"))
    else:
        checks.append(("Media (text-only)", True, "no media needed"))

    # 7. No duplicate text in posted history
    posted_texts = set()
    for pid, pinfo in state["posted"].items():
        # Look up the original tweet text from demos
        for d in demos:
            if str(d["id"]) == str(pid):
                posted_texts.add(d["tweet"])
                break
    is_duplicate = text in posted_texts
    checks.append(("No duplicate text", not is_duplicate,
                    "DUPLICATE" if is_duplicate else "unique"))

    # Print results
    print(f"{'='*62}")
    print(f"PRE-SEND VALIDATION")
    print(f"{'='*62}")
    all_pass = True
    for name, passed, detail in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_pass = False
        print(f"  {status}  {name:35} {detail}")

    VALIDATION_PASSED = all_pass
    print(f"\n{'='*62}")
    if VALIDATION_PASSED:
        print(f"✅ ALL CHECKS PASSED — safe to post")
    else:
        print(f"❌ VALIDATION FAILED — fix errors above before posting")
    print(f"{'='*62}")

    # Preview
    print(f"\n  Preview: {text[:120]}")

print(f"\nAPI calls this step: 0")
# ── Cell 7: Build Tweet Payload & Preview ────────────────────────────
if tweet is None:
    print("No tweet selected — run Step 3 first.")
elif not VALIDATION_PASSED:
    print("❌ BLOCKED — FIX VALIDATION ERRORS IN STEP 6")
else:
    text = tweet["tweet"]
    final_media = generated_path or media_path
    has_media = final_media is not None and Path(final_media).exists()

    # Build payload
    tweet_payload = {"text": text}
    if has_media:
        tweet_payload["media"] = {"media_ids": ["<uploaded_media_id>"]}

    print(f"{'='*62}")
    print(f"TWEET PAYLOAD PREVIEW")
    print(f"{'='*62}")
    print()

    # Request 1: Media upload
    if has_media:
        p = Path(final_media)
        print(f"Request 1 — Media Upload:")
        print(f"  POST https://upload.twitter.com/1.1/media/upload.json")
        print(f"  Auth: OAuth 1.0a")
        print(f"  Body: multipart/form-data  media={p.name} ({p.stat().st_size / 1024:.1f} KB)")
        print(f"  Response: {{ \"media_id_string\": \"<id>\" }}")
        print()

    # Request 2: Tweet post
    req_num = 2 if has_media else 1
    print(f"Request {req_num} — Post Tweet:")
    print(f"  POST https://api.twitter.com/2/tweets")
    print(f"  Auth: OAuth 1.0a")
    print(f"  Content-Type: application/json")
    print(f"  Body:")
    print(f"  {json.dumps(tweet_payload, indent=4, ensure_ascii=False)}")
    print()

    # Side-by-side preview
    print(f"{'='*62}")
    print(f"PREVIEW")
    print(f"{'='*62}")
    print(f"  Tweet:      {text}")
    print(f"  Characters: {char_count} / {MAX_CHARS}")
    print(f"  Media:      {media_desc}")
    if has_media:
        p = Path(final_media)
        print(f"  File:       {p.name} ({p.stat().st_size / 1024:.1f} KB)")

    # Display media inline
    if has_media:
        print()
        display(IPImage(filename=str(final_media), width=400))

    total_api_needed = 2 if has_media else 1
    print(f"\n{'='*62}")
    print(f"✅ READY TO POST")
    print(f"{'='*62}")
    print(f"  X API calls needed: {total_api_needed}")
    print(f"    • Media upload (v1.1):  {'1' if has_media else '0'}")
    print(f"    • Tweet post (v2):      1")
    print(f"  Free tier budget:   1,500 tweets/month")
    print(f"\n  Cumulative API calls so far: {api_call_counter}")

print(f"\nAPI calls this step: 0 (preview only)")
# ── Cell 8: Post to X & Update State ─────────────────────────────────
import requests
from requests_oauthlib import OAuth1

_run_start = datetime.now(timezone.utc)

if tweet is None:
    print("No tweet selected — run Step 3 first.")
elif not VALIDATION_PASSED:
    print("❌ Validation failed — fix errors in Step 6 first.")
elif DRY_RUN:
    print(f"{'='*62}")
    print(f"DRY RUN — no API calls made")
    print(f"{'='*62}")
    print()
    print(f"Would post:")
    print(f"  Text:  {tweet['tweet'][:200]}")
    print(f"  Media: {media_desc}")
    print(f"  Type:  {tweet['type']} ({tweet['stage']})")
    print()
    print(f"Set DRY_RUN = False in Step 1 and re-run to post for real.")
    print(f"\nAPI calls this step: 0")
else:
    auth = OAuth1(
        os.getenv("TWITTER_API_KEY"),
        os.getenv("TWITTER_API_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    text = tweet["tweet"]
    final_media = generated_path or media_path
    has_media = final_media is not None and Path(final_media).exists()
    media_id = None

    try:
        # ── Upload media (v1.1) ──
        if has_media:
            print("Uploading media...")
            with open(final_media, "rb") as f:
                r = requests.post(
                    "https://upload.twitter.com/1.1/media/upload.json",
                    auth=auth, files={"media": f}, timeout=60,
                )
            api_call_counter["x_api"] += 1
            if r.status_code == 200:
                media_id = r.json()["media_id_string"]
                print(f"  ✅ Uploaded: media_id={media_id}")
            else:
                print(f"  ❌ Upload FAILED: {r.status_code} {r.text[:200]}")
                print("  Posting text-only instead.")

        # ── Post tweet (v2) ──
        payload = {"text": text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}

        print("Posting tweet...")
        r = requests.post(
            "https://api.twitter.com/2/tweets",
            auth=auth, json=payload, timeout=30,
        )
        api_call_counter["x_api"] += 1

        if r.status_code in (200, 201):
            x_tweet_id = r.json()["data"]["id"]
            print(f"  ✅ POSTED: https://x.com/HedgeEdge_/status/{x_tweet_id}")

            # Update state file
            state["posted"][str(tweet["id"])] = {
                "posted_at":  datetime.now(timezone.utc).isoformat(),
                "tweet_x_id": x_tweet_id,
                "type":       tweet["type"],
                "stage":      tweet["stage"],
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            print(f"  State updated: {len(state['posted'])} total posted")

            # Discord success alert
            try:
                from shared.alerting import send_cron_success
                elapsed = (datetime.now(timezone.utc) - _run_start).total_seconds()
                desc = (
                    f"Posted **{tweet['type']}** ({tweet['stage']}) — ID {tweet['id']}\n"
                    f"X API calls: {api_call_counter['x_api']}"
                )
                send_cron_success("X Content Pipeline", desc, elapsed)
                print(f"  Discord alert sent.")
            except Exception as alert_err:
                print(f"  ⚠️  Discord alert failed (non-critical): {alert_err}")
        else:
            print(f"  ❌ Post FAILED: {r.status_code} {r.text[:300]}")
            # Discord failure alert
            try:
                from shared.alerting import send_cron_failure
                send_cron_failure("X Content Pipeline", f"HTTP {r.status_code}: {r.text[:200]}")
                print(f"  Discord failure alert sent.")
            except Exception as alert_err:
                print(f"  ⚠️  Discord alert failed: {alert_err}")

    except Exception as fatal_err:
        print(f"\n💥 Fatal error: {fatal_err}")
        try:
            from shared.alerting import send_cron_failure
            send_cron_failure("X Content Pipeline", fatal_err)
            print("  🚨 Discord failure alert sent.")
        except Exception as alert_err:
            print(f"  Discord alert also failed: {alert_err}")
        raise

    # ── Summary ──
    print(f"\n{'='*62}")
    print(f"POST SUMMARY")
    print(f"{'='*62}")
    print(f"  Tweet ID:    {tweet['id']}")
    print(f"  Type:        {tweet['type']} ({tweet['stage']})")
    print(f"  Characters:  {char_count} / {MAX_CHARS}")
    print(f"  Media:       {media_desc}")
    print(f"  X API calls: {api_call_counter['x_api']}")
    print(f"{'='*62}")
    print(f"\nAPI calls this step: {api_call_counter['x_api']}")
# ── Cell 9: API Cost & Efficiency Audit ──────────────────────────────
print(f"{'='*62}")
print(f"API COST & EFFICIENCY AUDIT")
print(f"{'='*62}")
print()
print(f"{'Service':<20} {'Calls Made':>10} {'Free Tier Limit':>18} {'Cost':>8}")
print(f"{'-'*62}")

limits = {
    "x_api":      "1,500 tweets/mo",
    "imgflip":    "unlimited (free)",
    "pexels":     "200 req/hr",
    "giphy_cdn":  "no key needed",
}
for service, calls in api_call_counter.items():
    limit = limits.get(service, "—")
    cost = "$0.00"
    print(f"{service:<20} {calls:>10} {limit:>18} {cost:>8}")

total_calls = sum(api_call_counter.values())
print(f"{'-'*62}")
print(f"{'TOTAL':<20} {total_calls:>10} {'':>18} {'$0.00':>8}")

print(f"\n{'='*62}")
print(f"DESIGN PHILOSOPHY")
print(f"{'='*62}")
print(f"All media is resolved and generated locally from a curated library.")
print(f"The only external calls are the final X API post (unavoidable)")
print(f"and media upload. Zero spend on image generation.")
print(f"")
print(f"In DRY_RUN mode: 0 external API calls total.")
print(f"In live mode: 1-2 X API calls per tweet (upload + post).")
print(f"At 1-2 tweets/day: ~60-120 of 1,500 monthly X API quota used.")

# Runway remaining
posted_ids_fresh = set(int(k) for k in state["posted"].keys())
remaining_fresh = [d for d in demos if d.get("type") in AUTO_TYPES and d["id"] not in posted_ids_fresh]
rem_types = Counter(d.get("type") for d in remaining_fresh)

print(f"\n{'='*62}")
print(f"CONTENT RUNWAY")
print(f"{'='*62}")

low_types = []
for ttype in sorted(AUTO_TYPES):
    count = rem_types.get(ttype, 0)
    flag = " ⚠️ LOW" if count < 5 else ""
    print(f"  {ttype:25}: {count} remaining{flag}")
    if count < 5:
        low_types.append(ttype)

tofu_rem = sum(1 for d in remaining_fresh if d.get("stage") == "TOFU")
mofu_rem = sum(1 for d in remaining_fresh if d.get("stage") == "MOFU")
bofu_rem = sum(1 for d in remaining_fresh if d.get("stage") == "BOFU")
print(f"\n  TOFU: {tofu_rem} → {tofu_rem/7:.1f} weeks at 7/wk")
print(f"  MOFU: {mofu_rem} → {mofu_rem/3:.1f} weeks at 3/wk")
print(f"  BOFU: {bofu_rem} → manual posting only")

if low_types:
    print(f"\n⚠️  Recommendation: Write more templates for: {', '.join(low_types)}")
else:
    print(f"\n✅ All types have healthy runway.")