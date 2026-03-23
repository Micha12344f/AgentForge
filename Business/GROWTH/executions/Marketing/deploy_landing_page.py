"""
Deploy Hedge Edge landing page to Vercel via API.
Usage:  python scripts/deploy_landing_page.py
"""

import sys, os

def _find_ws_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, 'shared')) and os.path.isdir(os.path.join(d, 'Business')):
            return d
        d = os.path.dirname(d)
    raise RuntimeError('Cannot locate workspace root')

sys.path.insert(0, _find_ws_root())

from shared.vercel_client import deploy_landing_page, wait_for_deploy


def main():
    print("⏳ Triggering Vercel deploy from latest main …")
    result = deploy_landing_page()
    print(f"   Deploy ID: {result['id']}")
    print(f"   Preview:   {result['url']}")

    print("⏳ Waiting for build …")
    final = wait_for_deploy(result["id"], timeout_s=180)
    if final["state"] == "READY":
        print(f"✅ LIVE  →  {final['url']}")
    else:
        print(f"❌ Deploy ended with state: {final['state']}")


if __name__ == "__main__":
    main()
