"""youtube_search_tool — search YouTube and return structured video metadata.

Wraps YouTube Data API v3 via google-api-python-client.

Cost note: one `search().list()` call costs 100 of the 10,000 daily quota units and
returns NO view counts (only video IDs + snippets). To get view counts we make a second
`videos().list(part="statistics")` call (1 unit) with the collected IDs and merge.

Identical queries are cached in-memory for the life of the process so repeated searches
within one session don't burn quota.
"""

from __future__ import annotations

import logging
from typing import Any

from googleapiclient.discovery import build

import config

log = logging.getLogger(__name__)

# Module-level cache: (query, max_results) -> result list. Lives for the process.
_CACHE: dict[tuple[str, int], list[dict[str, Any]]] = {}

# Lazily-built client so importing this module never touches the network.
_youtube = None


def _client():
    global _youtube
    if _youtube is None:
        # cache_discovery=False silences a noisy oauth2client file_cache warning.
        _youtube = build(
            "youtube", "v3", developerKey=config.YOUTUBE_API_KEY, cache_discovery=False
        )
    return _youtube


def youtube_search(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    """Search YouTube for videos matching `query`, with view counts merged in.

    Returns a list of dicts, each with:
        video_id, title, channel, view_count (int), published_at, url

    On any API error, logs a warning and returns an empty list rather than raising,
    so the orchestrator can degrade gracefully.
    """
    key = (query, max_results)
    if key in _CACHE:
        log.info("youtube_search cache hit: %r", query)
        return _CACHE[key]

    try:
        youtube = _client()

        # Step 1: search → video IDs + snippet (no statistics available here).
        search_resp = (
            youtube.search()
            .list(q=query, part="snippet", type="video", maxResults=max_results)
            .execute()
        )
        items = search_resp.get("items", [])
        video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]

        if not video_ids:
            _CACHE[key] = []
            return []

        # Step 2: fetch statistics (view counts) for the collected IDs — cheap, 1 unit.
        stats_resp = (
            youtube.videos()
            .list(part="statistics", id=",".join(video_ids))
            .execute()
        )
        views_by_id = {
            it["id"]: int(it.get("statistics", {}).get("viewCount", 0))
            for it in stats_resp.get("items", [])
        }

        # Merge snippet + statistics, preserving search-result order.
        results: list[dict[str, Any]] = []
        for it in items:
            vid = it.get("id", {}).get("videoId")
            if not vid:
                continue
            snip = it["snippet"]
            results.append(
                {
                    "video_id": vid,
                    "title": snip.get("title", ""),
                    "channel": snip.get("channelTitle", ""),
                    "view_count": views_by_id.get(vid, 0),
                    "published_at": snip.get("publishedAt", ""),
                    "url": f"https://www.youtube.com/watch?v={vid}",
                }
            )

        _CACHE[key] = results
        return results

    except Exception as exc:  # noqa: BLE001 — degrade gracefully, never crash orchestrator
        log.warning("youtube_search failed for %r: %s", query, exc)
        return []
