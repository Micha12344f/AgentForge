"""Create permanent Discord invite and update Short.io /discord link."""
import sys, os, requests, json
from dotenv import load_dotenv

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
load_dotenv(os.path.join(_WS_ROOT, ".env"))

token = os.getenv("DISCORD_BOT_TOKEN")
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

# Create permanent invite on welcome channel
channel_id = "1101261017528422450"  # 🤗-welcome
r = requests.post(
    f"https://discord.com/api/v10/channels/{channel_id}/invites",
    headers=headers,
    json={"max_age": 0, "max_uses": 0, "unique": True},
    timeout=10,
)
print(f"Create invite status: {r.status_code}")
data = r.json()
code = data.get("code", "")
invite_url = f"https://discord.gg/{code}"
print(f"Permanent invite: {invite_url}")

# Update Short.io /discord link to point to real invite
from shared.shortio_client import list_links, update_link

DOMAIN_ID = 1661144
links = list_links(domain_id=DOMAIN_ID, limit=150)
discord_link = None
for link in links:
    if link.get("path") == "discord":
        discord_link = link
        break

if discord_link:
    lid = discord_link.get("idString")
    old_url = discord_link.get("originalURL")
    result = update_link(lid, originalURL=invite_url)
    new_url = result.get("originalURL", "?")
    print(f"\nShort.io /discord updated:")
    print(f"  Old: {old_url}")
    print(f"  New: {new_url}")
    print(f"  Short URL: https://link.hedgedge.info/discord")
else:
    print("\nWARNING: No /discord link found in Short.io to update")
