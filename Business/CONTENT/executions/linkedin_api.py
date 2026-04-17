"""
linkedin_api.py — Full LinkedIn REST API wrapper for CONTENT agent.

Usage:
    from Business.CONTENT.executions.linkedin_api import LinkedInAPI
    api = LinkedInAPI()          # loads token from .env
    api.create_text_post("Hello LinkedIn!")
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve .env
# ---------------------------------------------------------------------------
_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


def _load_env(path: Path = _ENV_PATH) -> dict[str, str]:
    """Read key=value pairs from a .env file."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


# ---------------------------------------------------------------------------
# LinkedInAPI class
# ---------------------------------------------------------------------------

class LinkedInAPI:
    """Thin wrapper around the LinkedIn REST v2 / versioned APIs."""

    API_VERSION = "202604"
    REST_BASE = "https://api.linkedin.com/rest"
    V2_BASE = "https://api.linkedin.com/v2"

    def __init__(self, access_token: str | None = None):
        env = _load_env()
        self.token = access_token or env.get("LINKEDIN_ACCESS_TOKEN", "")
        if not self.token:
            raise RuntimeError("LINKEDIN_ACCESS_TOKEN not set in .env and not passed explicitly.")
        self._person_urn: str | None = None

    # -- helpers ----------------------------------------------------------

    def _headers(self, extra: dict | None = None) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    @staticmethod
    def _encode_urn(urn: str) -> str:
        return urllib.parse.quote(urn, safe="")

    def _request(self, method: str, url: str, body: dict | None = None,
                 headers: dict | None = None, raw_body: bytes | None = None) -> dict | str:
        hdrs = headers or self._headers()
        data = None
        if raw_body is not None:
            data = raw_body
        elif body is not None:
            data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                ct = resp.headers.get("Content-Type", "")
                raw = resp.read()
                if "application/json" in ct and raw:
                    return json.loads(raw)
                etag = resp.headers.get("ETag", "")
                if etag:
                    return {"_etag": etag.strip('"'), "_status": resp.status}
                return {"_status": resp.status, "_body": raw.decode(errors="replace")}
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode(errors="replace") if exc.fp else ""
            raise RuntimeError(
                f"LinkedIn API {method} {url} -> {exc.code}: {err_body}"
            ) from exc

    # -- identity ---------------------------------------------------------

    def get_profile(self) -> dict:
        """GET /v2/userinfo — returns name, email, sub, picture."""
        return self._request("GET", f"{self.V2_BASE}/userinfo")

    @property
    def person_urn(self) -> str:
        if self._person_urn is None:
            profile = self.get_profile()
            self._person_urn = f"urn:li:person:{profile['sub']}"
        return self._person_urn

    # -- posts ------------------------------------------------------------

    def create_text_post(self, text: str, visibility: str = "PUBLIC") -> dict:
        body = {
            "author": self.person_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return self._request("POST", f"{self.REST_BASE}/posts", body=body)

    def create_image_post(self, text: str, image_urn: str,
                          alt_text: str = "", visibility: str = "PUBLIC") -> dict:
        body = {
            "author": self.person_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "altText": alt_text,
                    "id": image_urn,
                },
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return self._request("POST", f"{self.REST_BASE}/posts", body=body)

    def create_article_post(self, text: str, url: str, title: str,
                            description: str = "", thumbnail_urn: str = "",
                            visibility: str = "PUBLIC") -> dict:
        article: dict = {"source": url, "title": title, "description": description}
        if thumbnail_urn:
            article["thumbnail"] = thumbnail_urn
        body = {
            "author": self.person_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {"article": article},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return self._request("POST", f"{self.REST_BASE}/posts", body=body)

    def create_video_post(self, text: str, video_urn: str,
                          title: str = "", visibility: str = "PUBLIC") -> dict:
        body = {
            "author": self.person_urn,
            "commentary": text,
            "visibility": visibility,
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "title": title,
                    "id": video_urn,
                },
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        return self._request("POST", f"{self.REST_BASE}/posts", body=body)

    def get_post(self, post_urn: str) -> dict:
        return self._request("GET", f"{self.REST_BASE}/posts/{self._encode_urn(post_urn)}")

    def get_posts(self, count: int = 10, sort_by: str = "LAST_MODIFIED") -> dict:
        encoded = self._encode_urn(self.person_urn)
        url = f"{self.REST_BASE}/posts?author={encoded}&q=author&count={count}&sortBy={sort_by}"
        return self._request("GET", url)

    def update_post(self, post_urn: str, commentary: str) -> dict:
        url = f"{self.REST_BASE}/posts/{self._encode_urn(post_urn)}"
        hdrs = self._headers({"X-RestLi-Method": "PARTIAL_UPDATE"})
        body = {"patch": {"$set": {"commentary": commentary}}}
        return self._request("POST", url, body=body, headers=hdrs)

    def delete_post(self, post_urn: str) -> dict:
        return self._request("DELETE", f"{self.REST_BASE}/posts/{self._encode_urn(post_urn)}")

    # -- images -----------------------------------------------------------

    def upload_image(self, file_path: str) -> str:
        """Initialize upload, PUT binary, return image URN."""
        init_body = {"initializeUploadRequest": {"owner": self.person_urn}}
        resp = self._request("POST", f"{self.REST_BASE}/images?action=initializeUpload",
                             body=init_body)
        upload_url = resp["value"]["uploadUrl"]
        image_urn = resp["value"]["image"]

        with open(file_path, "rb") as fh:
            image_bytes = fh.read()

        hdrs = self._headers()
        hdrs["Content-Type"] = "application/octet-stream"
        self._request("PUT", upload_url, headers=hdrs, raw_body=image_bytes)
        return image_urn

    # -- videos -----------------------------------------------------------

    def upload_video(self, file_path: str, upload_captions: bool = False,
                     upload_thumbnail: bool = False) -> str:
        """Multi-part video upload. Returns video URN."""
        file_size = os.path.getsize(file_path)
        init_body = {
            "initializeUploadRequest": {
                "owner": self.person_urn,
                "fileSizeBytes": file_size,
                "uploadCaptions": upload_captions,
                "uploadThumbnail": upload_thumbnail,
            }
        }
        resp = self._request("POST", f"{self.REST_BASE}/videos?action=initializeUpload",
                             body=init_body)
        val = resp["value"]
        video_urn = val["video"]
        upload_token = val.get("uploadToken", "")
        instructions = val["uploadInstructions"]

        etags: list[str] = []
        with open(file_path, "rb") as fh:
            for part in instructions:
                first = part["firstByte"]
                last = part["lastByte"]
                chunk_size = last - first + 1
                fh.seek(first)
                chunk = fh.read(chunk_size)
                hdrs = {"Content-Type": "application/octet-stream"}
                result = self._request("PUT", part["uploadUrl"],
                                       headers=hdrs, raw_body=chunk)
                etags.append(result.get("_etag", ""))

        finalize_body = {
            "finalizeUploadRequest": {
                "video": video_urn,
                "uploadToken": upload_token,
                "uploadedPartIds": etags,
            }
        }
        self._request("POST", f"{self.REST_BASE}/videos?action=finalizeUpload",
                       body=finalize_body)
        return video_urn

    # -- comments ---------------------------------------------------------

    def create_comment(self, post_urn: str, text: str) -> dict:
        url = f"{self.REST_BASE}/socialActions/{self._encode_urn(post_urn)}/comments"
        body = {
            "actor": self.person_urn,
            "object": post_urn,
            "message": {"text": text},
        }
        return self._request("POST", url, body=body)

    def get_comments(self, post_urn: str, count: int = 10, start: int = 0) -> dict:
        url = (f"{self.REST_BASE}/socialActions/{self._encode_urn(post_urn)}"
               f"/comments?count={count}&start={start}")
        return self._request("GET", url)

    def delete_comment(self, post_urn: str, comment_id: str) -> dict:
        actor = self._encode_urn(self.person_urn)
        url = (f"{self.REST_BASE}/socialActions/{self._encode_urn(post_urn)}"
               f"/comments/{comment_id}?actor={actor}")
        return self._request("DELETE", url)

    # -- reactions --------------------------------------------------------

    def create_reaction(self, entity_urn: str,
                        reaction_type: str = "LIKE") -> dict:
        actor = self._encode_urn(self.person_urn)
        url = f"{self.REST_BASE}/reactions?actor={actor}"
        # Derive root activity URN from entity
        body = {
            "root": entity_urn,
            "reactionType": reaction_type,
        }
        return self._request("POST", url, body=body)

    def get_reactions(self, entity_urn: str, count: int = 10, start: int = 0) -> dict:
        encoded = self._encode_urn(entity_urn)
        url = f"{self.REST_BASE}/reactions/(entity:{encoded})?q=entity&count={count}&start={start}"
        return self._request("GET", url)

    def delete_reaction(self, entity_urn: str) -> dict:
        actor = self._encode_urn(self.person_urn)
        encoded = self._encode_urn(entity_urn)
        url = f"{self.REST_BASE}/reactions/(actor:{actor},entity:{encoded})"
        return self._request("DELETE", url)

    # -- social metadata --------------------------------------------------

    def get_social_metadata(self, post_urn: str) -> dict:
        return self._request("GET",
                             f"{self.REST_BASE}/socialMetadata/{self._encode_urn(post_urn)}")

    def batch_get_social_metadata(self, urns: list[str]) -> dict:
        encoded_list = ",".join(self._encode_urn(u) for u in urns)
        url = f"{self.REST_BASE}/socialMetadata?ids=List({encoded_list})"
        return self._request("GET", url)

    def set_comments_state(self, post_urn: str, state: str = "CLOSED") -> dict:
        actor = self._encode_urn(self.person_urn)
        url = f"{self.REST_BASE}/socialMetadata/{self._encode_urn(post_urn)}?actor={actor}"
        body = {"patch": {"$set": {"commentsState": state}}}
        return self._request("POST", url, body=body)


# ---------------------------------------------------------------------------
# Quick CLI smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    api = LinkedInAPI()
    profile = api.get_profile()
    print(f"Authenticated as: {profile.get('name')} ({profile.get('email')})")
    print(f"Person URN: {api.person_urn}")

    if len(sys.argv) > 1 and sys.argv[1] == "--post":
        text = " ".join(sys.argv[2:]) or "Hello from AgentForge!"
        result = api.create_text_post(text)
        print(f"Post created: {result}")
