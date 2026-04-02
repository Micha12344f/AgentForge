# X Management

> X is the primary awareness channel for Hedge Edge. Use this workflow for every thread, standalone post, and automated TOFU or MOFU post.

## Purpose

- Turn X into the top-of-funnel engine for Hedge Edge
- Keep posting safe, consistent, and reviewable
- Separate content generation from publishing so broken posts never hit the API

## Core Workflow

1. Choose the content lane: TOFU awareness, MOFU education, or manual real-time commentary.
2. If using the automated library, run `executions/Marketing/auto_tweet.py` to select the next unposted asset and prepare media.
3. Validate and publish via `executions/Marketing/x_manager.py`.
4. If posting a thread, rely on the state file to resume safely rather than restarting the full run.
5. Log what shipped by keeping the auto-tweet state file current and reviewing posted IDs before reruns.

## Scripts

| Script | Use |
|---|---|
| `executions/Marketing/auto_tweet.py` | Picks the next automatable tweet, resolves media, enforces stage limits, and hands off to `x_manager.py` |
| `executions/Marketing/x_manager.py` | Validates text and media locally, posts threads or single tweets, and manages delete/resume flows |
| `executions/Marketing/Twitter_reply_system.py` | Reply workflow for mentions and outbound engagement |
| `executions/Marketing/tw_search_reply.py` | Search-led reply discovery |
| `executions/Marketing/x_content_pipeline.py` | Local notebook-style workspace for reviewing pipeline state and assets |

## Safety Rules

- Validate locally before any X request.
- Never write tweet text directly in a PowerShell inline `-c` command. Dollar signs get mangled.
- Keep the state file for every live thread or automated run until the post succeeds.
- Wait at least 25 seconds between tweets in a thread.
- After a 403 from X, wait 20 minutes before retrying.
- Do not post uncaptained TOFU meme templates. Blank templates are for generation only.

## Operating Modes

### Automated posting

- Use for TOFU and MOFU queue-based content.
- `auto_tweet.py` prevents same-day duplicates for the same stage unless you intentionally override with `--force`.
- Use `--preview` or `--dry-run` before live posting when checking a new asset batch.

### Manual single posts or threads

- Use `x_manager.py` with a thread JSON file when the post is handcrafted.
- Use `--action dry-run` first for anything new, especially threads with media.

### Reply engagement

- Use replies for relevance and discovery, not spam.
- Prioritize prop-firm traders, platform operators, and adjacent trading conversations.

## Environment Requirements

- X auth: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`
- Meme captioning: `IMGFLIP_USERNAME`, `IMGFLIP_PASSWORD`
- Atmospheric fallback images: `PEXELS_API_KEY`

## File Locations

### Content data (pipeline state and tweet library)

| File | Path |
|---|---|
| Tweet content library | `resources/Marketing/x-pipeline/tweet_demos_100.json` |
| Posted-tweet state | `resources/Marketing/x-pipeline/auto_tweet_state.json` |

`tweet_demos_100.json` holds 55 ready-to-post demos across TOFU (funny_meme, gif_meme, viral_hook), MOFU (industry_take, stat_truth, uncomfortable_truth), and BOFU (direct_cta) types. Add new entries here when the library needs refreshing.

`auto_tweet_state.json` tracks every post that has shipped. `auto_tweet.py` reads this on startup to skip already-posted IDs. Never delete this file — append-only.

### Media assets

| Folder | Contents |
|---|---|
| `resources/Marketing/x-assets/library/manifest.json` | Master index of all local images and GIFs |
| `resources/Marketing/x-assets/library/tofu/images/` | 17 blank meme templates (Imgflip IDs encoded in filename) |
| `resources/Marketing/x-assets/library/tofu/gifs/` | 18 GIF files keyed by mood (stressed, facepalm, rip_wallet, etc.) |
| `resources/Marketing/x-assets/library/mofu/` | 30 atmospheric Pexels photos for MOFU posts |
| `resources/Marketing/x-assets/generated/` | Output folder for Imgflip-captioned memes and Pillow-captioned GIFs |
| `resources/Marketing/x-assets/Hedge-Edge-Logo.png` | Brand logo used for BOFU CTA posts (add file here when available) |

## Review Checklist

- The post matches the voice in `resources/Marketing/x-strategy.md`.
- The CTA matches the funnel stage.
- Media exists and is sized correctly.
- Text has no HTML entities, broken dollar signs, mojibake, or duplicated thread content.
- If rerunning, the state file proves what already posted.