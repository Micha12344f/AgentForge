#!/usr/bin/env python3
"""
call_transcriber.py — Sales Agent Call Transcription & Analysis

Transcribe sales/demo recordings with Groq Whisper (free) and generate
structured AI summaries with Llama 3.3, storing results in Notion demo_log.

Usage:
    python call_transcriber.py --action transcribe --file recording.mp3 --uid cX8F6cBQ3RKMmuwQz7EGcS
    python call_transcriber.py --action transcribe --file recording.mp3 --lead "Nicky Kivuvani"
    python call_transcriber.py --action transcribe --file recording.mp3 --lead "Nicky Kivuvani" --chunk
    python call_transcriber.py --action transcribe-bulk --folder ./recordings
    python call_transcriber.py --action summary-only --uid cX8F6cBQ3RKMmuwQz7EGcS
"""

import sys, os, argparse, glob, json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from shared.groq_client import transcribe_audio, summarise_sales_call
from shared.notion_client import query_db, update_row, log_task

try:
    from shared.groq_client import transcribe_audio_chunked
except ImportError:
    def transcribe_audio_chunked(*args, **kwargs):
        raise NotImplementedError(
            "transcribe_audio_chunked not yet in shared/groq_client.py — "
            "split your file to < 25 MB chunks manually or ask @orchestrator to add it."
        )

AGENT = "Sales"
AUDIO_EXTS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg", ".flac"}


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _find_demo_row(uid: str = "", lead: str = "") -> dict | None:
    """Find a demo_log row by Cal.com UID (in Notes) or Lead Name."""
    rows = query_db("demo_log")
    if uid:
        for r in rows:
            notes = r.get("Notes") or r.get("Name") or ""
            if uid in notes:
                return r
    if lead:
        lead_lower = lead.lower()
        for r in rows:
            name = (r.get("Name") or r.get("Lead Name") or "").lower()
            email = (r.get("Email") or "").lower()
            if lead_lower in name or lead_lower in email:
                return r
    return None


def _save_local(transcript: str, summary: str, identifier: str) -> str:
    """Save transcript + summary to scripts/output/ for archival."""
    ws = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
    out_dir = os.path.join(ws, "scripts", "output")
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = identifier.replace(" ", "_")[:40]
    path = os.path.join(out_dir, f"transcript_{safe_id}_{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Call Transcript — {identifier}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("## Transcript\n\n")
        f.write(transcript + "\n\n")
        f.write("## AI Summary\n\n")
        f.write(summary + "\n")
    return path


# ──────────────────────────────────────────────
#  Actions
# ──────────────────────────────────────────────

def transcribe(args):
    """Transcribe a single audio file → AI summary → Notion."""
    if not args.file or not os.path.isfile(args.file):
        print(f"❌ Audio file not found: {args.file}")
        return

    identifier = args.uid or args.lead or os.path.basename(args.file)
    size_mb = os.path.getsize(args.file) / (1024 * 1024)

    print("=" * 60)
    print("  🎙️  CALL TRANSCRIPTION")
    print("=" * 60)
    print(f"  File:     {os.path.basename(args.file)} ({size_mb:.1f} MB)")
    print(f"  Match by: {'UID ' + args.uid if args.uid else 'Lead: ' + (args.lead or 'filename')}")

    # ── Step 1: Transcribe ──
    print("\n  ⏳ Transcribing with Groq Whisper...")
    try:
        if args.chunk or size_mb > 25:
            result = transcribe_audio_chunked(args.file)
        else:
            result = transcribe_audio(args.file)
        transcript = result.get("text", "")
        duration = result.get("duration", 0)
    except Exception as e:
        print(f"  ❌ Transcription failed: {e}")
        log_task(AGENT, f"Transcription failed: {identifier}", "Error", "P1", str(e))
        return

    word_count = len(transcript.split())
    print(f"  ✅ Transcribed: {word_count} words, {duration:.0f}s duration")

    # ── Step 2: AI Summary ──
    print("  ⏳ Generating AI summary...")
    try:
        summary = summarise_sales_call(transcript, lead_name=args.lead or identifier)
    except Exception as e:
        print(f"  ⚠️  Summary failed (saving transcript only): {e}")
        summary = "(Summary generation failed)"

    # ── Step 3: Save locally ──
    local_path = _save_local(transcript, summary, identifier)
    print(f"  💾 Saved: {os.path.basename(local_path)}")

    # ── Step 4: Update Notion ──
    row = _find_demo_row(uid=args.uid or "", lead=args.lead or "")
    if row:
        # Notion rich_text limit is 2000 chars — truncate if needed
        updates = {
            "Transcript": transcript[:2000],
            "Summary":    summary[:2000],
        }
        if args.recording_url:
            updates["Recording URL"] = args.recording_url
        update_row(row["_id"], "demo_log", updates)
        print(f"  📝 Notion updated: {row.get('Name', row['_id'][:8])}")
    else:
        print(f"  ⚠️  No matching demo_log row found — transcript saved locally only")
        print(f"       Use --uid or --lead to match a booking")

    print("─" * 60)
    log_task(AGENT, f"Transcribed call: {identifier}", "Complete", "P2",
             f"{word_count} words, {duration:.0f}s")


def transcribe_bulk(args):
    """Scan a folder for audio files and transcribe all of them."""
    folder = args.folder or "."
    if not os.path.isdir(folder):
        print(f"❌ Folder not found: {folder}")
        return

    files = []
    for ext in AUDIO_EXTS:
        files.extend(glob.glob(os.path.join(folder, f"*{ext}")))

    print("=" * 60)
    print("  🎙️  BULK TRANSCRIPTION")
    print("=" * 60)
    print(f"  Folder: {folder}")
    print(f"  Found:  {len(files)} audio files")

    if not files:
        print("\n  No audio files found.")
        print("─" * 60)
        return

    success, failed = 0, 0
    for i, f in enumerate(sorted(files), 1):
        print(f"\n  [{i}/{len(files)}] {os.path.basename(f)}")
        try:
            # Build a minimal args-like object
            class BulkArgs:
                file = f
                uid = ""
                lead = os.path.splitext(os.path.basename(f))[0]
                chunk = False
                recording_url = ""
            transcribe(BulkArgs())
            success += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed += 1

    print(f"\n{'─' * 60}")
    print(f"  Done: {success} transcribed, {failed} failed")
    log_task(AGENT, "Bulk transcription", "Complete", "P2",
             f"{success}/{len(files)} files")


def summary_only(args):
    """Re-generate AI summary from an existing transcript in Notion."""
    row = _find_demo_row(uid=args.uid or "", lead=args.lead or "")
    if not row:
        print(f"❌ No demo_log row found for UID={args.uid} / Lead={args.lead}")
        return

    transcript = row.get("Transcript", "")
    if not transcript:
        print(f"❌ No transcript found in row: {row.get('Name', '?')}")
        print("   Run --action transcribe first to transcribe the audio.")
        return

    print("=" * 60)
    print("  🧠 RE-GENERATING AI SUMMARY")
    print("=" * 60)
    print(f"  Row: {row.get('Name', '?')}")

    lead_name = row.get("Name") or row.get("Lead Name") or args.lead or ""
    summary = summarise_sales_call(transcript, lead_name=lead_name)
    update_row(row["_id"], "demo_log", {"Summary": summary[:2000]})

    print(f"  ✅ Summary updated ({len(summary)} chars)")
    print(f"\n{summary}")
    print("─" * 60)
    log_task(AGENT, f"Re-summarised: {lead_name}", "Complete", "P3", f"{len(summary)} chars")


# ──────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sales Call Transcription & Analysis")
    parser.add_argument("--action", required=True,
                        choices=["transcribe", "transcribe-bulk", "summary-only"])
    parser.add_argument("--file", help="Path to audio file")
    parser.add_argument("--folder", help="Folder of audio files (for bulk)")
    parser.add_argument("--uid", default="", help="Cal.com booking UID to match")
    parser.add_argument("--lead", default="", help="Lead name to match in demo_log")
    parser.add_argument("--chunk", action="store_true",
                        help="Force chunked transcription (for files >25 MB)")
    parser.add_argument("--recording-url", default="", dest="recording_url",
                        help="URL of the recording (stored in Notion)")
    args = parser.parse_args()

    dispatch = {
        "transcribe": transcribe,
        "transcribe-bulk": transcribe_bulk,
        "summary-only": summary_only,
    }
    dispatch[args.action](args)
