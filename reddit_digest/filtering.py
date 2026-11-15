from __future__ import annotations

from .client import RedditPost


def filter_posts(posts: list[RedditPost], keywords: list[str], min_score: int = 0) -> list[RedditPost]:
    terms = [term.casefold().strip() for term in keywords if term.strip()]
    result: list[RedditPost] = []
    for post in posts:
        if post.score < min_score:
            continue
        haystack = f"{post.title}\n{post.text}".casefold()
        if terms and not any(term in haystack for term in terms):
            continue
        result.append(post)
    return sorted(result, key=lambda item: (item.score, item.comments), reverse=True)

