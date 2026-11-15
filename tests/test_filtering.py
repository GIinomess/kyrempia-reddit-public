from reddit_digest.client import RedditPost
from reddit_digest.filtering import filter_posts


def post(title: str, score: int = 10) -> RedditPost:
    return RedditPost("x", "stocks", title, "", "https://reddit.com/x", None, score, 1)


def test_filter_matches_title_and_orders_by_score() -> None:
    result = filter_posts([post("Oil supply warning", 2), post("Oil market update", 10)], ["oil"], 2)
    assert [item.title for item in result] == ["Oil market update", "Oil supply warning"]


def test_filter_rejects_irrelevant_and_low_score_posts() -> None:
    result = filter_posts([post("Gaming news", 100), post("Bitcoin rumor", 1)], ["bitcoin"], 2)
    assert result == []

