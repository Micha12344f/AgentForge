"""
railway.py — Railway CLI wrapper for the email-marketing agent.

Functions:
    check_railway_status()       → Verify auth + linked project
    trigger_email_send()         → Run railway_email_send.py via Railway CLI
    parse_send_output(output)    → Extract sent/error counts from CLI output

Pattern proven on 2026-03-08:
    $ railway run python scripts/Railway/railway_email_send.py
    → Railway injects all env vars automatically (RESEND_API_KEY, NOTION_API_KEY, etc.)
    → Output line: [Done] Sent=N Errors=N in X.Xs
    → Discord success alert fires automatically from within railway_email_send.py

Prerequisites:
    - Railway CLI installed:  railway --version
    - Logged in:              railway whoami
    - Project linked:         railway status  (must show Email-Send-Service / production)
    - Workspace root in PATH: cwd = workspace root (auto-detected)
"""

import re
import subprocess
from pathlib import Path
import os, sys

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

# ── Workspace root ─────────────────────────────────────────────────────────────
_EMAIL_SCRIPT = Path("scripts/Railway/railway_email_send.py")


# ──────────────────────────────────────────────────────────────────────────────
#  Status / Auth Checks
# ──────────────────────────────────────────────────────────────────────────────

def check_railway_status():
    """Verify Railway CLI is installed, authenticated, and project-linked.

    Returns dict:
        {
          "cli_version": "4.30.5",
          "logged_in_as": "ryansossion@gmail.com",
          "project": "Email-Send-Service",
          "environment": "production",
          "service": "Email-Send-Service",
          "ready": True,
        }
    Raises RuntimeError if CLI is missing or not logged in.
    """
    # 1. Check CLI is installed
    try:
        ver_out = subprocess.check_output(
            ["railway", "--version"], text=True, cwd=str(_WS_ROOT)
        ).strip()
        cli_version = ver_out.split()[-1] if ver_out else "unknown"
    except FileNotFoundError:
        raise RuntimeError(
            "Railway CLI not found. Install it: https://docs.railway.app/develop/cli"
        )

    # 2. Check auth + project link
    status_out = subprocess.run(
        ["railway", "whoami"],
        capture_output=True, text=True, cwd=str(_WS_ROOT)
    ).stdout

    status_out2 = subprocess.run(
        ["railway", "status"],
        capture_output=True, text=True, cwd=str(_WS_ROOT)
    ).stdout

    combined = status_out + "\n" + status_out2

    # Parse logged-in email
    email_match = re.search(r"Logged in as ([\w.@+-]+)", combined)
    logged_in_as = email_match.group(1) if email_match else None

    # Parse project name
    project_match = re.search(r"Project:\s*(.+)", combined)
    project = project_match.group(1).strip() if project_match else None

    # Parse environment
    env_match = re.search(r"Environment:\s*(.+)", combined)
    environment = env_match.group(1).strip() if env_match else None

    # Parse service
    service_match = re.search(r"Service:\s*(.+)", combined)
    service = service_match.group(1).strip() if service_match else None

    if not logged_in_as:
        raise RuntimeError("Not logged into Railway. Run: railway login")
    if not project:
        raise RuntimeError("No Railway project linked. Run: railway link")

    result = {
        "cli_version":  cli_version,
        "logged_in_as": logged_in_as,
        "project":      project,
        "environment":  environment,
        "service":      service,
        "ready":        True,
    }
    print(f"Railway status: {result}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
#  Email Send Trigger
# ──────────────────────────────────────────────────────────────────────────────

def trigger_email_send(dry_run=True, timeout=180):
    """Run the production email send script via Railway CLI.

    Railway injects all env vars (RESEND_API_KEY, NOTION_API_KEY, etc.)
    from the linked service automatically — no .env loading required here.

    Args:
        dry_run:  If True, only verify Railway is ready and prints what would
                  run — does NOT execute. Set dry_run=False to actually send.
        timeout:  Max seconds to wait for the script to complete (default 180).

    Returns dict:
        {
          "sent":    1,
          "errors":  0,
          "elapsed": "37.1s",
          "output":  "<full stdout>",
          "success": True,
        }

    Raises:
        RuntimeError  if Railway is not ready (CLI missing / not logged in)
        subprocess.CalledProcessError  if the script exits non-zero
    """
    # Always verify auth first
    check_railway_status()

    cmd = ["railway", "run", "python", str(_EMAIL_SCRIPT)]
    print(f"Command: {' '.join(cmd)}")
    print(f"CWD:     {_WS_ROOT}")

    if dry_run:
        print("[DRY RUN] Railway env verified. Not executing — set dry_run=False to send.")
        return {"sent": 0, "errors": 0, "elapsed": "0s", "output": "", "success": True, "dry_run": True}

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_WS_ROOT),
        timeout=timeout,
    )

    output = result.stdout + result.stderr
    print(output)

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=output)

    parsed = parse_send_output(output)
    parsed["output"] = output
    return parsed


def parse_send_output(output):
    """Extract sent/error counts and elapsed time from railway_email_send.py output.

    Expected output line (from railway_email_send.py):
        [Done] Sent=1 Errors=0 in 37.1s

    Returns dict:
        {"sent": 1, "errors": 0, "elapsed": "37.1s", "success": True}
    """
    match = re.search(r"Sent=(\d+)\s+Errors=(\d+)\s+in\s+([\d.]+s)", output)
    if match:
        return {
            "sent":    int(match.group(1)),
            "errors":  int(match.group(2)),
            "elapsed": match.group(3),
            "success": int(match.group(2)) == 0,
        }
    # Fallback: couldn't parse — return raw
    return {"sent": -1, "errors": -1, "elapsed": "unknown", "success": False}
