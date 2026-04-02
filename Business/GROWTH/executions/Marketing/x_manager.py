#!/usr/bin/env python3
"""
x_manager.py - Content Engine Agent: X (Twitter) Management Skill

Handles all X posting for Hedge Edge with strict pre-send validation.
No API request is ever made until content passes all local checks.

Usage:
    python x_manager.py --action dry-run --thread-file thread.json
    python x_manager.py --action post-thread --thread-file thread.json
    python x_manager.py --action resume --state-file _thread_state.json
    python x_manager.py --action post-tweet --text "Your tweet text"
    python x_manager.py --action delete --tweet-id 1234567890
"""

import sys, os, json, argparse, time, html, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
import requests
from requests_oauthlib import OAuth1

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "Business" / "GROWTH" / "resources" / ".env", override=True)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def _auth():
    return OAuth1(
        os.getenv("TWITTER_API_KEY"),
        os.getenv("TWITTER_API_SECRET"),
        os.getenv("TWITTER_ACCESS_TOKEN"),
        os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

# ---------------------------------------------------------------------------
# Pre-send validator (ZERO API calls)
# ---------------------------------------------------------------------------
MAX_CHARS = 280
URL_CHAR_WEIGHT = 23
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_VIDEO_BYTES = 512 * 1024 * 1024
VALID_MEDIA_EXT = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webp"}

# Common Mojibake signatures produced when UTF-8 is read as cp1252
MOJIBAKE_PATTERNS = [
    "\u00e2\u0080\u0094",  # em dash corrupted
    "\u00e2\u0080\u0099",  # right single quote corrupted
    "\u00e2\u0080\u009c",  # left double quote corrupted
    "\u00e2\u0080\u009d",  # right double quote corrupted
    "\u00c3\u00b0\u00c5\u00b8",  # emoji prefix corrupted
    "â€",   # most common Mojibake marker
    "â€",
    "â€œ",
    "ðŸ",   # corrupted emoji prefix
    "\ufffd",  # Unicode replacement character
]

def _count_chars(text):
    url_pattern = re.compile(r"https?://\S+")
    cleaned = url_pattern.sub("X" * URL_CHAR_WEIGHT, text)
    return len(cleaned)

def validate_tweet(index, text, media_path=None):
    errors = []
    warnings = []

    # 1. Mojibake / encoding corruption  must be first
    for marker in MOJIBAKE_PATTERNS:
        if marker in text:
            errors.append(
                f"ENCODING CORRUPTION: text contains Mojibake marker {repr(marker)}  "
                "JSON file was not read as UTF-8. Fix: open(file, encoding='utf-8')"
            )
            break  # one error is enough to flag this

    # 2. Character count
    char_count = _count_chars(text)
    if char_count > MAX_CHARS:
        errors.append(f"TOO LONG: {char_count} chars (max {MAX_CHARS})")

    # 3. HTML entity check
    decoded = html.unescape(text)
    if decoded != text:
        errors.append(f"HTML ENTITIES detected  decode before sending: {repr(text[:80])}")

    # 4. Broken dollar sign from shell escaping
    if r"\$" in text:
        errors.append(r"BROKEN DOLLAR SIGN: contains \$  write tweet in a .py file, not a shell -c command")

    # 5. Double-escaped newlines
    if r"\\n" in text:
        errors.append(r"DOUBLE-ESCAPED NEWLINE: contains \\n  use \n instead")

    # 6. Warn on bare $ (might be intentional)
    dollar_matches = re.findall(r"\$\d+", text)
    if dollar_matches:
        warnings.append(f"Contains {dollar_matches}  confirm dollar amounts render correctly")

    # 7. Media file checks
    if media_path:
        p = ROOT / media_path if not Path(media_path).is_absolute() else Path(media_path)
        if not p.exists():
            errors.append(f"MEDIA NOT FOUND: {media_path}")
        else:
            size = p.stat().st_size
            ext = p.suffix.lower()
            if ext not in VALID_MEDIA_EXT:
                errors.append(f"UNSUPPORTED MEDIA FORMAT: {ext}")
            elif ext in (".jpg", ".jpeg", ".png", ".webp") and size > MAX_IMAGE_BYTES:
                errors.append(f"IMAGE TOO LARGE: {size/1e6:.1f}MB (max 5MB)")
            elif ext == ".mp4" and size > MAX_VIDEO_BYTES:
                errors.append(f"VIDEO TOO LARGE: {size/1e6:.0f}MB (max 512MB)")
            # 8. Blank template guard: images from assets/library/ have no captions burned in
            #    Only assets/generated/ contains captioned output -- block anything else
            str_p = p.as_posix()
            if "assets/library/tofu/" in str_p and ext in (".jpg", ".jpeg", ".png"):
                errors.append(
                    "BLANK TEMPLATE DETECTED: image is from TOFU library (uncaptioned template). "
                    "Captioning must succeed before posting. Check meme_maker.py or Imgflip credentials."
                )

    return char_count, errors, warnings


def validate_all(tweets):
    print("\n=== PRE-SEND VALIDATION ===")
    all_pass = True
    seen_texts = set()

    for i, t in enumerate(tweets, 1):
        text = t.get("text", "")
        media = t.get("media_path")
        char_count, errors, warnings = validate_tweet(i, text, media)

        if text in seen_texts:
            errors.append("DUPLICATE: identical text to a previous tweet in this thread")
        seen_texts.add(text)

        status = "OK" if not errors else "FAIL"
        media_str = f" | Media: {media}" if media else ""
        print(f"Tweet {i}: [{status}] {char_count} chars{media_str}")
        # Print actual text preview so corruption is visible
        print(f"         Preview: {text[:80].replace(chr(10), ' ')}")
        for e in errors:
            print(f"         ERROR: {e}")
            all_pass = False
        for w in warnings:
            print(f"         WARN:  {w}")

    print()
    if all_pass:
        print("ALL TWEETS PASS -- safe to post\n")
    else:
        print("VALIDATION FAILED -- fix errors above before posting\n")
    return all_pass


# ---------------------------------------------------------------------------
# API operations
# ---------------------------------------------------------------------------
def upload_media(media_path):
    p = ROOT / media_path if not Path(media_path).is_absolute() else Path(media_path)
    with open(p, "rb") as f:
        data = f.read()
    r = requests.post(
        "https://upload.twitter.com/1.1/media/upload.json",
        auth=_auth(), files={"media": data}, timeout=60,
    )
    if r.status_code == 200:
        return r.json()["media_id_string"]
    raise RuntimeError(f"Media upload failed {r.status_code}: {r.text}")


def post_tweet(text, reply_to_id=None, media_ids=None):
    payload = {"text": text}
    if reply_to_id:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}
    if media_ids:
        payload["media"] = {"media_ids": media_ids}
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=_auth(), json=payload, timeout=30,
    )
    if r.status_code in (200, 201):
        return r.json()["data"]["id"]
    raise RuntimeError(f"Post failed {r.status_code}: {r.text}")


def delete_tweet(tweet_id):
    r = requests.delete(
        f"https://api.twitter.com/2/tweets/{tweet_id}",
        auth=_auth(), timeout=15,
    )
    if r.status_code == 200:
        print(f"  Deleted {tweet_id}")
        return True
    print(f"  Delete failed {r.status_code}: {r.text}")
    return False


# ---------------------------------------------------------------------------
# State file helpers -- always UTF-8
# ---------------------------------------------------------------------------
def load_state(state_file):
    p = Path(state_file)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_state(state_file, state):
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def build_state(thread_id, tweets):
    return {
        "thread_id": thread_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "tweets": [
            {
                "index": i + 1,
                "status": "pending",
                "id": None,
                "text": t["text"],
                "media_path": t.get("media_path"),
            }
            for i, t in enumerate(tweets)
        ],
    }


# ---------------------------------------------------------------------------
# Thread posting engine
# ---------------------------------------------------------------------------
DELAY_BETWEEN_TWEETS = 25  # seconds


def run_thread(tweets, state_file, dry_run=False, reply_to_first=None):
    if not validate_all(tweets):
        sys.exit(1)

    if dry_run:
        print("DRY RUN complete -- no requests made.")
        return

    state = load_state(state_file)
    if state is None:
        state = build_state(Path(state_file).stem, tweets)
        save_state(state_file, state)

    # Seed reply chain from last posted tweet
    last_id = reply_to_first
    for entry in state["tweets"]:
        if entry["status"] == "posted" and entry["id"]:
            last_id = entry["id"]

    for entry in state["tweets"]:
        if entry["status"] == "posted":
            print(f"Tweet {entry['index']}: already posted (ID: {entry['id']}) -- skipping")
            continue

        text = entry["text"]
        media_path = entry.get("media_path")

        print(f"\n=== Posting tweet {entry['index']} ===")
        print(f"  {text[:120].replace(chr(10), ' ')}")

        media_ids = None
        if media_path:
            print(f"  Uploading: {media_path}")
            media_ids = [upload_media(media_path)]

        tweet_id = post_tweet(text, reply_to_id=last_id, media_ids=media_ids)
        print(f"  Posted -- ID: {tweet_id}")

        entry["status"] = "posted"
        entry["id"] = tweet_id
        last_id = tweet_id
        save_state(state_file, state)

        if entry["index"] < len(state["tweets"]):
            print(f"  Waiting {DELAY_BETWEEN_TWEETS}s...")
            time.sleep(DELAY_BETWEEN_TWEETS)

    print("\nTHREAD COMPLETE")
    for entry in state["tweets"]:
        print(f"  Tweet {entry['index']}: {entry['id']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True,
        choices=["post-thread", "dry-run", "resume", "post-tweet", "delete"])
    parser.add_argument("--thread-file")
    parser.add_argument("--state-file", default="_thread_state.json")
    parser.add_argument("--reply-to")
    parser.add_argument("--text")
    parser.add_argument("--tweet-id")
    args = parser.parse_args()

    if args.action in ("post-thread", "dry-run"):
        if not args.thread_file:
            print("--thread-file required"); sys.exit(1)
        with open(args.thread_file, encoding="utf-8") as f:
            data = json.load(f)
        tweets = data["tweets"]
        run_thread(tweets, state_file=args.state_file,
                   dry_run=(args.action == "dry-run"),
                   reply_to_first=args.reply_to)

    elif args.action == "resume":
        state = load_state(args.state_file)
        if not state:
            print(f"State file not found: {args.state_file}"); sys.exit(1)
        tweets = state["tweets"]
        run_thread(tweets, state_file=args.state_file, reply_to_first=args.reply_to)

    elif args.action == "post-tweet":
        if not args.text:
            print("--text required"); sys.exit(1)
        _, errors, warnings = validate_tweet(1, args.text)
        for e in errors: print(f"ERROR: {e}")
        if errors: sys.exit(1)
        for w in warnings: print(f"WARN: {w}")
        tweet_id = post_tweet(args.text)
        print(f"Posted -- ID: {tweet_id}")

    elif args.action == "delete":
        if not args.tweet_id:
            print("--tweet-id required"); sys.exit(1)
        delete_tweet(args.tweet_id)


if __name__ == "__main__":
    main()
