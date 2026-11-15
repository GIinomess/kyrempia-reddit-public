from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class RedditPost:
    post_id: str
    subreddit: str
    title: str
    text: str
    url: str
    published_at: str | None
    score: int
    comments: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class RedditClient:
    """Small, read-only client for Reddit's official OAuth API."""

    token_url = "https://www.reddit.com/api/v1/access_token"
    api_root = "https://oauth.reddit.com"

    def __init__(self, client_id: str, client_secret: str, user_agent: str, delay: float = 1.1):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.delay = max(0.0, delay)
        self._token: str | None = None

    @classmethod
    def from_environment(cls) -> "RedditClient":
        values = {key: os.environ.get(key, "").strip() for key in (
            "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"
        )}
        missing = [key for key, value in values.items() if not value]
        if missing:
            raise RuntimeError("Missing environment variables: " + ", ".join(missing))
        return cls(**{
            "client_id": values["REDDIT_CLIENT_ID"],
            "client_secret": values["REDDIT_CLIENT_SECRET"],
            "user_agent": values["REDDIT_USER_AGENT"],
        })

    def _request_json(self, request: Request) -> dict:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
        if not isinstance(payload, dict):
            raise RuntimeError("Reddit returned an unexpected response")
        return payload

    def access_token(self) -> str:
        if self._token:
            return self._token
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        body = urlencode({"grant_type": "client_credentials"}).encode()
        request = Request(
            self.token_url,
            data=body,
            headers={
                "Authorization": f"Basic {auth}",
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        payload = self._request_json(request)
        token = payload.get("access_token")
        if not token:
            raise RuntimeError("Reddit did not return an access token")
        self._token = str(token)
        return self._token

    def newest(self, subreddit: str, limit: int = 25) -> list[RedditPost]:
        subreddit = subreddit.strip().strip("/")
        if not subreddit:
            return []
        request = Request(
            f"{self.api_root}/r/{subreddit}/new.json?limit={max(1, min(limit, 100))}",
            headers={
                "Authorization": f"Bearer {self.access_token()}",
                "User-Agent": self.user_agent,
            },
        )
        payload = self._request_json(request)
        children = payload.get("data", {}).get("children", [])
        posts: list[RedditPost] = []
        for child in children if isinstance(children, list) else []:
            data = child.get("data", {}) if isinstance(child, dict) else {}
            post_id = str(data.get("id") or "")
            title = str(data.get("title") or "").strip()
            if not post_id or not title:
                continue
            created = data.get("created_utc")
            published = None
            if created is not None:
                published = datetime.fromtimestamp(float(created), timezone.utc).isoformat()
            permalink = str(data.get("permalink") or "")
            posts.append(RedditPost(
                post_id=post_id,
                subreddit=subreddit,
                title=title,
                text=str(data.get("selftext") or "").strip()[:4000],
                url=f"https://www.reddit.com{permalink}" if permalink.startswith("/") else str(data.get("url") or ""),
                published_at=published,
                score=int(data.get("score") or 0),
                comments=int(data.get("num_comments") or 0),
            ))
        time.sleep(self.delay)
        return posts

