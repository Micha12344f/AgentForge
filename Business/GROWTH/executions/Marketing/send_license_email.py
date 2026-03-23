#!/usr/bin/env python3
"""
Hedge Edge — License Confirmation Email Sender
================================================
Sends license key + download links to a customer via Resend.
No Notion dependency at send-time (fast path).

Usage:
    python send_license_email.py --to user@example.com --key HE-XXXX-XXXX --name "John"
    
    # Or import as module:
    from send_license_email import send_license_confirmation
    result = send_license_confirmation("user@example.com", "HE-XXXX-XXXX", name="John")
"""

import os
import sys
import hmac
import hashlib
import argparse
import html as html_mod
import requests
from urllib.parse import quote

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
from dotenv import load_dotenv
load_dotenv(os.path.join(_WS_ROOT, ".env"))

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
UNSUBSCRIBE_SECRET = os.getenv("UNSUBSCRIBE_SECRET", "")
FROM_ADDR = "Hedge Edge <hello@hedgedge.info>"
REPLY_TO = "reply@hedgedge.info"
SUBJECT = "Your Hedge Edge License Key"
RESEND_TEMPLATE_ID = "cb865ed2-575b-461a-9bb1-c0d9c6a4e08a"  # Resend dashboard template

GITHUB_REPO = "Micha12344f/Hedge-Edge-App"
APP_DOWNLOAD_URL = "https://link.hedgedge.info/download-app"
MT5_ZIP_URL = "https://link.hedgedge.info/mt5-experts"
# UTM-tagged homepage link — included in email to track email → web attribution
DASHBOARD_UTM_URL = (
    "https://hedgedge.info"
    "?utm_source=email&utm_medium=drip&utm_campaign=license-key"
)


def _build_unsubscribe_token(email: str) -> str:
    if not UNSUBSCRIBE_SECRET:
        return ""
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(),
        email.lower().strip().encode(),
        hashlib.sha256,
    ).hexdigest()


def _build_unsubscribe_url(email: str) -> str:
    email_clean = email.lower().strip()
    token = _build_unsubscribe_token(email_clean)
    if not token:
        return ""
    return f"https://hedgedge.info/unsubscribe?email={quote(email_clean)}&token={token}"


def _build_unsubscribe_api_url(email: str) -> str:
    email_clean = email.lower().strip()
    token = _build_unsubscribe_token(email_clean)
    if not token:
        return ""
    return f"https://hedgedge.info/api/handle-unsubscribe?email={quote(email_clean)}&token={token}"


def build_html(license_key: str, name: str = "", unsub_url: str = "") -> str:
    greeting = f"Hi {html_mod.escape(name)}," if name else "Hi there,"
    safe_key = html_mod.escape(license_key)
    unsub_html = ""
    if unsub_url:
        safe_unsub = html_mod.escape(unsub_url)
        unsub_html = f'''<p style="margin:8px 0 0;font-size:11px;"><a href="{safe_unsub}" style="color:#aaaaaa;text-decoration:underline;">Unsubscribe</a></p>'''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Hedge Edge License Key</title>
</head>
<body style="margin:0;padding:0;background-color:#f7f7f7;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f7f7f7;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#ffffff;border-radius:8px;border:1px solid #e5e5e5;">
          <tr>
            <td style="padding:28px 36px 20px;border-bottom:1px solid #eeeeee;">
              <span style="font-size:24px;font-weight:700;color:#111111;letter-spacing:-0.3px;">Hedge</span><span style="font-size:24px;font-weight:700;color:#16a34a;letter-spacing:-0.3px;">Edge</span>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 36px;">
              <p style="margin:0 0 16px;font-size:16px;color:#333333;line-height:1.6;">{greeting}</p>
              <p style="margin:0 0 20px;font-size:15px;color:#555555;line-height:1.7;">Thank you for your purchase. Your Hedge Edge license is ready. Here is your license key:</p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
                <tr>
                  <td style="background-color:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:16px 20px;text-align:center;">
                    <span style="font-family:'Courier New',Courier,monospace;font-size:18px;font-weight:700;color:#15803d;letter-spacing:1px;">{safe_key}</span>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 8px;font-size:15px;color:#555555;line-height:1.7;">Enter this key when you first open the Hedge Edge app, and again when you attach the Expert Advisors in MT5.</p>
              <p style="margin:0 0 24px;font-size:13px;color:#888888;line-height:1.5;">Keep this key safe. It is tied to your account and can be used on up to 2 devices.</p>
              <p style="margin:0 0 12px;font-size:15px;font-weight:600;color:#333333;">Your Downloads</p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
                <tr>
                  <td style="padding:10px 0;border-bottom:1px solid #f0f0f0;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-size:14px;color:#555555;line-height:1.5;"><strong style="color:#333333;">Hedge Edge App</strong><br><span style="font-size:13px;color:#888888;">Windows desktop application</span></td>
                        <td align="right" style="vertical-align:middle;"><a href="{APP_DOWNLOAD_URL}" style="display:inline-block;padding:8px 20px;font-size:13px;font-weight:600;color:#ffffff;background-color:#16a34a;border-radius:5px;text-decoration:none;">Download</a></td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td style="padding:10px 0;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-size:14px;color:#555555;line-height:1.5;"><strong style="color:#333333;">MT5 Expert Advisors</strong><br><span style="font-size:13px;color:#888888;">Includes EAs, DLLs, and installation guide</span></td>
                        <td align="right" style="vertical-align:middle;"><a href="{MT5_ZIP_URL}" style="display:inline-block;padding:8px 20px;font-size:13px;font-weight:600;color:#ffffff;background-color:#16a34a;border-radius:5px;text-decoration:none;">Download</a></td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 12px;font-size:15px;font-weight:600;color:#333333;">Quick Start</p>
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
                <tr><td style="padding:3px 0;font-size:14px;color:#555555;line-height:1.6;">1. Install the Hedge Edge app and enter your license key</td></tr>
                <tr><td style="padding:3px 0;font-size:14px;color:#555555;line-height:1.6;">2. Extract the MT5 ZIP and copy files to your MT5 terminal</td></tr>
                <tr><td style="padding:3px 0;font-size:14px;color:#555555;line-height:1.6;">3. Attach the EAs to your charts and enter your license key</td></tr>
                <tr><td style="padding:3px 0;font-size:14px;color:#555555;line-height:1.6;">4. The app will connect to MT5 automatically</td></tr>
              </table>
              <p style="margin:0 0 16px;font-size:14px;color:#555555;line-height:1.7;">Need help? Just reply to this email.</p>
              <p style="margin:0;font-size:13px;color:#888888;line-height:1.6;">Want to manage your subscription or access the web dashboard? <a href="{DASHBOARD_UTM_URL}" style="color:#16a34a;text-decoration:underline;">Sign in to your account</a>.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 36px 24px;border-top:1px solid #eeeeee;">
              <p style="margin:0 0 6px;font-size:12px;color:#999999;line-height:1.5;">You are receiving this because you purchased a Hedge Edge license.</p>
              <p style="margin:0;font-size:11px;color:#aaaaaa;line-height:1.5;">Hedge Edge | hedgedge.info</p>
              {unsub_html}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_plain_text(license_key: str, name: str = "", unsub_url: str = "") -> str:
    greeting = f"Hi {name}," if name else "Hi there,"
    unsub_line = f"\n\n---\nUnsubscribe: {unsub_url}" if unsub_url else ""
    return f"""{greeting}

Thank you for your purchase. Your Hedge Edge license is ready.

YOUR LICENSE KEY: {license_key}

Enter this key when you first open the Hedge Edge app, and again when you attach the Expert Advisors in MT5. Keep it safe - it works on up to 2 devices.

DOWNLOADS:

Hedge Edge App (Windows):
{APP_DOWNLOAD_URL}

MT5 Expert Advisors (EAs, DLLs, and install guide):
{MT5_ZIP_URL}

QUICK START:
1. Install the Hedge Edge app and enter your license key
2. Extract the MT5 ZIP and copy files to your MT5 terminal
3. Attach the EAs to your charts and enter your license key
4. The app will connect to MT5 automatically

Want to manage your account? Sign in at:
{DASHBOARD_UTM_URL}

Need help? Just reply to this email.

-- Hedge Edge
hedgedge.info{unsub_line}"""


def send_license_confirmation(to: str, license_key: str, name: str = "") -> dict:
    """Send the license confirmation email via Resend. No Notion dependency."""
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not set in .env")

    unsub_url = _build_unsubscribe_url(to)
    api_unsub_url = _build_unsubscribe_api_url(to)

    html_body = build_html(license_key, name=name, unsub_url=unsub_url)
    text_body = build_plain_text(license_key, name=name, unsub_url=unsub_url)

    payload = {
        "from": FROM_ADDR,
        "to": [to],
        "reply_to": REPLY_TO,
        "subject": SUBJECT,
        "html": html_body,
        "text": text_body,
        "tags": [
            {"name": "campaign", "value": "license-confirmation"},
            {"name": "type", "value": "transactional"},
        ],
    }

    # RFC 8058 List-Unsubscribe (required by Gmail/Yahoo since Feb 2024)
    if api_unsub_url:
        payload["headers"] = {
            "List-Unsubscribe": f"<{api_unsub_url}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Hedge Edge license confirmation email")
    parser.add_argument("--to", required=True, help="Recipient email")
    parser.add_argument("--key", required=True, help="License key")
    parser.add_argument("--name", default="", help="Recipient name")
    args = parser.parse_args()

    result = send_license_confirmation(args.to, args.key, name=args.name)
    print(f"Sent! Resend ID: {result.get('id', 'unknown')}")
