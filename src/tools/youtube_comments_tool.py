"""youtube_comments_tool — fetch the top comments on a YouTube video.

Wraps YouTube Data API v3 `commentThreads().list()` (1 quota unit per call). Used to ground a
plan in what the real audience of comparable Shorts actually says — their language, reactions,
pain points and desires. This is the "audience signal" source (it replaces the Reddit tool: the
viewers of comparable videos are a more on-target audience than a tangential subreddit, and it
needs no second API credential).

Identical (video_id, limit) requests are cached in-memory for the life of the process.
"""

from __future__ import annotations

import logging
from typing import Any

from googleapiclient.discovery import build

import config

log = logging.getLogger(__name__)

_TEXT_LIMIT = 500

# Module-level cache: (video_id, limit) -> result list. Lives for the process.
_CACHE: dict[tuple[str, int], list[dict[str, Any]]] = {}

# Lazily-built client so importing this module never touches the network.
_youtube = None


def _client():
    global _youtube
    if _youtube is None:
        _youtube = build(
            "youtube", "v3", developerKey=config.YOUTUBE_API_KEY, cache_discovery=False
        )
    return _youtube


def youtube_comments(video_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Fetch the top comments on a YouTube video.

    Args:
        video_id: the `video_id` from a youtube_search result.
        limit: how many top (relevance-ordered) comments to return.

    Returns a list of dicts, each with:
        author, text (truncated ~500 chars), like_count (int), video_id

    On any API error — including comments being disabled on the video — logs a warning and
    returns an empty list rather than raising, so the orchestrator can degrade gracefully.
    """
    key = (video_id, limit)
    if key in _CACHE:
        log.info("youtube_comments cache hit: %s", video_id)
        return _CACHE[key]

    try:
        resp = (
            _client()
            .commentThreads()
            .list(
                part="snippet",
                videoId=video_id,
                order="relevance",
                maxResults=limit,
                textFormat="plainText",
            )
            .execute()
        )

        results: list[dict[str, Any]] = []
        for item in resp.get("items", []):
            snip = item["snippet"]["topLevelComment"]["snippet"]
            results.append(
                {
                    "author": snip.get("authorDisplayName", ""),
                    "text": (snip.get("textDisplay", "") or "")[:_TEXT_LIMIT],
                    "like_count": int(snip.get("likeCount", 0)),
                    "video_id": video_id,
                }
            )

        _CACHE[key] = results
        return results

    except Exception as exc:  # noqa: BLE001 — degrade gracefully, never crash orchestrator
        log.warning("youtube_comments failed for %s: %s", video_id, exc)
        return []
