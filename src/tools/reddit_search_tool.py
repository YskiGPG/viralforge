"""reddit_search_tool — search subreddit discussions and return structured results.

Wraps the Reddit API via PRAW (read-only). Used to ground plans in what real audiences
are actually talking about around a topic.

Identical queries are cached in-memory for the life of the process.
"""

from __future__ import annotations

import logging
from typing import Any

import praw

import config

log = logging.getLogger(__name__)

_SELFTEXT_LIMIT = 500

# Module-level cache: (query, subreddit, limit) -> result list.
_CACHE: dict[tuple[str, str, int], list[dict[str, Any]]] = {}

_reddit = None


def _client():
    global _reddit
    if _reddit is None:
        _reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
        )
        _reddit.read_only = True
    return _reddit


def reddit_search(query: str, subreddit: str = "all", limit: int = 10) -> list[dict[str, Any]]:
    """Search Reddit for discussions matching `query`.

    Searches within `subreddit` (default "all"). Returns a list of dicts, each with:
        title, score (int), num_comments (int), subreddit, url, selftext (truncated ~500 chars)

    On any API error, logs a warning and returns an empty list rather than raising.
    """
    key = (query, subreddit, limit)
    if key in _CACHE:
        log.info("reddit_search cache hit: %r in r/%s", query, subreddit)
        return _CACHE[key]

    try:
        reddit = _client()
        sub = reddit.subreddit(subreddit)

        results: list[dict[str, Any]] = []
        for post in sub.search(query, sort="relevance", limit=limit):
            selftext = (post.selftext or "")[:_SELFTEXT_LIMIT]
            results.append(
                {
                    "title": post.title,
                    "score": int(post.score),
                    "num_comments": int(post.num_comments),
                    "subreddit": str(post.subreddit),
                    "url": f"https://www.reddit.com{post.permalink}",
                    "selftext": selftext,
                }
            )

        _CACHE[key] = results
        return results

    except Exception as exc:  # noqa: BLE001 — degrade gracefully, never crash orchestrator
        log.warning("reddit_search failed for %r in r/%s: %s", query, subreddit, exc)
        return []
