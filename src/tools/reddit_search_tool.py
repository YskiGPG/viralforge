"""reddit_search_tool — search subreddit discussions and return structured results.

To be implemented in Week 1. Wraps the Reddit API via PRAW (read-only).
"""

from typing import Any


def reddit_search(query: str, subreddit: str = "all", limit: int = 10) -> list[dict[str, Any]]:
    """Search Reddit for discussions matching `query`.

    Returns a list of dicts with at least: title, score, num_comments, url.
    """
    raise NotImplementedError("Implement in Week 1.")
