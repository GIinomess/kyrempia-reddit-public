from __future__ import annotations

import argparse
import json
import os

from .client import RedditClient
from .filtering import filter_posts


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Reddit topic digest")
    parser.add_argument("--keywords", default="", help="comma-separated topic keywords")
    parser.add_argument("--min-score", type=int, default=0)
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    subreddits = [item.strip() for item in os.environ.get("REDDIT_SUBREDDITS", "").split(",") if item.strip()]
    if not subreddits:
        parser.error("REDDIT_SUBREDDITS is empty")
    client = RedditClient.from_environment()
    posts = []
    for subreddit in subreddits:
        posts.extend(client.newest(subreddit, args.limit))
    keywords = args.keywords.split(",") if args.keywords else []
    selected = filter_posts(posts, keywords, args.min_score)
    print(json.dumps([post.to_dict() for post in selected], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

