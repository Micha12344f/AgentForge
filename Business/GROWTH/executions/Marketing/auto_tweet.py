#!/usr/bin/env python3
"""
auto_tweet.py - Automated single-tweet pipeline for Hedge Edge

Reads tweet_demos_100.json, picks the next unposted automatable tweet,
sources the right image, validates, and posts via x_manager.

Types: funny_meme, gif_meme, viral_hook, industry_take, stat_truth, uncomfortable_truth, direct_cta

Usage:
    python auto_tweet.py --stage tofu --type funny_meme --dry-run   # generate image + validate, no X post
    python auto_tweet.py --stage tofu --type funny_meme --preview   # generate image + open locally, zero X calls
    python auto_tweet.py --stage tofu --type gif_meme   --preview   # GIF preview
    python auto_tweet.py --stage tofu --type funny_meme             # post for real
    python auto_tweet.py --status
"""

import sys, json, argparse, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

def _find_ws_root():
    import os as _os
    d = _os.path.dirname(_os.path.abspath(__file__))
    for _ in range(15):
        if _os.path.isfile(_os.path.join(d, 'shared', 'notion_client.py')) and _os.path.isdir(_os.path.join(d, 'Business')):
            return d
        d = _os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

_WS = _find_ws_root()
ROOT = Path(_WS)
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "Business" / "GROWTH" / "resources" / ".env", override=True)

GROWTH_RES = ROOT / "Business" / "GROWTH" / "resources" / "Marketing"
DEMOS_FILE = GROWTH_RES / "x-pipeline" / "tweet_demos_100.json"
STATE_FILE = GROWTH_RES / "x-pipeline" / "auto_tweet_state.json"
LOGO_PATH  = GROWTH_RES / "x-assets" / "Hedge-Edge-Logo.png"
X_MANAGER  = ROOT / "Business" / "GROWTH" / "executions" / "Marketing" / "x_manager.py"
AUTO_TYPES = {"funny_meme", "gif_meme", "viral_hook", "industry_take", "stat_truth", "uncomfortable_truth", "direct_cta"}


def load_demos():
    with open(DEMOS_FILE, encoding="utf-8") as f:
        return json.load(f)["demos"]


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"posted": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def pick_tweet(demos, state, stage_filter=None, type_filter=None):
    posted_ids = set(int(k) for k in state["posted"].keys())

    # Build set of meme template_ids used in the last 7 days -- avoid visual repetition
    recent_cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_templates = set()
    for tid, info in state["posted"].items():
        if info.get("posted_at", "") >= recent_cutoff:
            if info.get("template_id"):
                recent_templates.add(str(info["template_id"]))

    def _passes_filters(demo):
        if demo["id"] in posted_ids:
            return False
        if demo.get("type") not in AUTO_TYPES:
            return False
        if stage_filter and demo.get("stage", "").lower() != stage_filter.lower():
            return False
        if type_filter and demo.get("type", "") != type_filter.lower():
            return False
        return True

    # First pass: prefer demos whose template hasn't been used this week
    for demo in demos:
        if not _passes_filters(demo):
            continue
        tid = str(demo.get("meme_template_id", ""))
        if tid and tid in recent_templates:
            continue  # skip -- same template posted in last 7 days
        return demo

    # Second pass: all remaining use recent templates -- fall back to sequential
    for demo in demos:
        if _passes_filters(demo):
            return demo

    return None


def resolve_image(demo):
    """Resolve image from local curated library. No external API calls."""
    image_type   = demo.get("image_type", "none")
    image_needed = demo.get("image_needed", False)
    stage        = demo.get("stage", "TOFU").upper()

    if not image_needed or image_type in ("none", None):
        return None, "no image"

    LIB = ROOT / "Business" / "GROWTH" / "resources" / "Marketing" / "x-assets" / "library"
    MANIFEST = LIB / "manifest.json"
    if MANIFEST.exists():
        with open(MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {}

    if image_type == "meme":
        template_id = str(demo.get("meme_template_id", ""))
        boxes = demo.get("meme_boxes", [])
        # Always caption via Imgflip first (free, zero cost) -- local blank is display-only
        from shared.meme_maker import caption_meme
        path, captioned = caption_meme(template_id, boxes)
        if captioned:
            return path, "meme (Imgflip captioned)"
        # Fallback: return local blank template if Imgflip fails
        for entry in manifest.get("tofu_images", []):
            if entry.get("template_id") == template_id:
                local = LIB / "tofu" / "images" / entry["file"]
                if local.exists():
                    return str(local), f"local meme template (uncaptioned): {entry.get('template_name', template_id)}"
        return path, "meme (uncaptioned)"

    if image_type == "gif":
        mood   = demo.get("gif_mood", "stressed")
        top    = demo.get("gif_top", "")
        bottom = demo.get("gif_bottom", "")
        # Look in local library
        for entry in manifest.get("tofu_gifs", []):
            if entry.get("mood") == mood:
                local = LIB / "tofu" / "gifs" / entry["file"]
                if local.exists():
                    from shared.gif_captioner import caption_gif
                    path, ok = caption_gif(str(local), top, bottom)
                    label = "local GIF (Pillow captioned)" if ok else "GIF captioning failed"
                    return path, label
        # Fallback: CDN
        from shared.gif_finder import find_gif
        from shared.gif_captioner import caption_gif
        url = find_gif(mood)
        if not url:
            return None, f"no GIF found for mood: {mood}"
        path, ok = caption_gif(url, top, bottom)
        return path, "GIF (CDN fallback)" if ok else "GIF captioning failed"

    if image_type == "logo":
        return (str(LOGO_PATH) if LOGO_PATH.exists() else None), "Hedge Edge logo"

    if image_type == "atmospheric":
        # Check for forced image override mapping
        import os, random
        force_img = os.environ.get("FORCE_IMAGE")
        if force_img:
            local = LIB / "mofu" / force_img
            if local.exists():
                return str(local), f"local atmospheric (FORCED): {force_img}"

        # Tag-aware MOFU image selection: match image mood to tweet type
        tweet_type = demo.get("type", "")
        mofu_entries = manifest.get("mofu", [])
        FIGURE_TAGS = {"anonymous", "shadow", "mysterious", "boardroom", "executive", "faceless", "dark", "power"}
        MARKET_TAGS = {"trading", "financial", "chart", "city", "night", "stock", "wall street", "bank"}
        if tweet_type in ("industry_take", "uncomfortable_truth"):
            preferred = [e for e in mofu_entries if FIGURE_TAGS & set(t.lower() for t in e.get("tags", []))]
        elif tweet_type == "stat_truth":
            preferred = [e for e in mofu_entries if MARKET_TAGS & set(t.lower() for t in e.get("tags", []))]
        else:
            preferred = []
        pool = preferred if preferred else mofu_entries
        if pool:
            pick = random.choice(pool)
            local = LIB / "mofu" / pick["file"]
            if local.exists():
                return str(local), f"local atmospheric: {pick['file']} by {pick.get('photographer', '?')}"
        # Fallback: Pexels API
        from shared.image_finder import get_image_for_tweet
        path = get_image_for_tweet(demo.get("type", ""))
        return path, "atmospheric (fallback)" if path else "no image"
    return None, f"unknown image_type: {image_type}"


def run(args):
    demos = load_demos()
    state = load_state()

    if args.status:
        posted = state["posted"]
        print(f"Posted: {len(posted)} / {len([d for d in demos if d.get('type') in AUTO_TYPES])} automatable tweets")
        for tid, info in sorted(posted.items(), key=lambda x: x[1].get("posted_at", "")):
            print(f"  ID {tid:3}: {info.get('type',''):25} X/{info.get('tweet_x_id','?')} @ {info.get('posted_at','')[:16]}")
        remaining = [d for d in demos if str(d["id"]) not in posted and d.get("type") in AUTO_TYPES]
        print(f"Remaining automatable: {len(remaining)}")
        return

    # --- Daily post limit: 1 TOFU + 1 MOFU per calendar day (UTC) ---
    # Prevents accidental double-posts from retried runs or automation bugs.
    # Use --force to override when manually intentional.
    if not args.dry_run and not getattr(args, 'force', False):
        today = datetime.now(timezone.utc).date().isoformat()
        stage_filter = (args.stage or "").lower()
        for tid, info in state["posted"].items():
            posted_date = info.get("posted_at", "")[:10]
            posted_stage = info.get("stage", "").lower()
            if posted_date == today and (not stage_filter or posted_stage == stage_filter):
                print(
                    f"BLOCKED: A {posted_stage.upper()} tweet was already posted today "
                    f"(ID {tid}, X/{info.get('tweet_x_id','?')})."
                )
                print("")
                print("  Deleted it from X and need to replace it?")
                print(f"    1. python auto_tweet.py --unlog {tid}   (clears it from the log)")
                print(f"    2. python auto_tweet.py --stage {posted_stage} --force   (bypasses today block)")
                print("")
                print("  Just want a second post on the same day?")
                print(f"    python auto_tweet.py --stage {posted_stage} --force")
                return

    tweet = pick_tweet(demos, state, stage_filter=args.stage, type_filter=args.type)
    if not tweet:
        print("No unposted tweets found matching those filters.")
        return

    print(f"\n{'='*62}")
    print(f"ID {tweet['id']} | {tweet['stage']} | {tweet['type']}")
    print(f"{'='*62}")
    print(tweet["tweet"])
    print()

    img_path, img_desc = resolve_image(tweet)
    print(f"Image: {img_desc}")
    if img_path:
        print(f"  Path: {img_path}")
    print()

    if args.preview:
        if img_path and Path(img_path).exists():
            import subprocess as sp
            sp.Popen(["explorer", str(Path(img_path))])
            print("Opened in Explorer. Zero X API calls made.")
        else:
            print("No image generated.")
        return

    # Build single-tweet thread file for x_manager
    entry = {"index": 1, "text": tweet["tweet"]}
    if img_path and Path(img_path).exists():
        try:
            rel = Path(img_path).relative_to(ROOT)
            entry["media_path"] = str(rel).replace("\\", "/")
        except ValueError:
            entry["media_path"] = img_path

    thread_data = {"thread_id": f"auto-{tweet['id']}", "tweets": [entry]}
    thread_file = ROOT / f"_auto_{tweet['id']}.json"
    state_file  = ROOT / f"_auto_state_{tweet['id']}.json"

    with open(thread_file, "w", encoding="utf-8") as f:
        json.dump(thread_data, f, indent=2, ensure_ascii=False)

    action = "dry-run" if args.dry_run else "post-thread"
    result = subprocess.run(
        [sys.executable, str(X_MANAGER), "--action", action,
         "--thread-file", str(thread_file), "--state-file", str(state_file)],
        cwd=str(ROOT)
    )

    x_tweet_id = None
    if not args.dry_run and state_file.exists():
        with open(state_file, encoding="utf-8") as f:
            st = json.load(f)
        entries = st.get("tweets", [])
        if entries and entries[0].get("status") == "posted":
            x_tweet_id = entries[0].get("id")

    thread_file.unlink(missing_ok=True)
    state_file.unlink(missing_ok=True)

    if args.dry_run:
        print("Dry-run complete. Image generated locally, no X POST made.")
        return

    if result.returncode == 0 and x_tweet_id:
        entry = {
            "posted_at":  datetime.now(timezone.utc).isoformat(),
            "tweet_x_id": x_tweet_id,
            "type":       tweet["type"],
            "stage":      tweet["stage"],
        }
        # Save template_id so pick_tweet can avoid same-template repetition
        if tweet.get("meme_template_id"):
            entry["template_id"] = str(tweet["meme_template_id"])
        state["posted"][str(tweet["id"])] = entry
        save_state(state)
        print(f"Logged. Total posted: {len(state['posted'])}")
    else:
        print("Post failed -- not logged. Fix and retry.")


def main():
    parser = argparse.ArgumentParser(description="Hedge Edge Auto Tweet Pipeline")
    parser.add_argument("--stage",   help="tofu | mofu | bofu")
    parser.add_argument("--type",    help="funny_meme | gif_meme | viral_hook | industry_take | stat_truth | uncomfortable_truth | direct_cta")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--status",  action="store_true")
    parser.add_argument("--force",   action="store_true",
                        help="Bypass the daily post limit (for manual corrections after deleting a tweet)")
    parser.add_argument("--unlog",   metavar="ID",
                        help="Remove a tweet demo ID from the posted log (use after deleting a bad tweet from X)")
    args = parser.parse_args()
    if args.unlog:
        state = load_state()
        demo_id = str(args.unlog)
        if demo_id in state["posted"]:
            entry = state["posted"].pop(demo_id)
            save_state(state)
            print(f"Unlogged demo ID {demo_id} (was X/{entry.get('tweet_x_id','?')}, posted {entry.get('posted_at','?')[:10]}).")
            print("Daily limit cleared for its stage. Safe to re-post.")
        else:
            print(f"Demo ID {demo_id} not found in posted log.")
            print("Current log:", list(state["posted"].keys()))
        return
    run(args)

if __name__ == "__main__":
    main()
