"""youtube_search_tool — search YouTube and return structured video metadata.

To be implemented in Week 1. Wraps YouTube Data API v3 via google-api-python-client.
Remember: a search call costs 100 quota units (of 10,000/day), so cache where you can.
"""

from typing import Any


def youtube_search(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    """Search YouTube for videos matching `query`.

    Returns a list of dicts with at least: video_id, title, channel, view_count.
    """
    raise NotImplementedError("Implement in Week 1.")
