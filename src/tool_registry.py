"""tool_registry — exposes the data Tools to Claude as SDK tool-use definitions.

Keeps the Anthropic tool schemas next to the dispatch map, so the orchestrator's message loop
stays small: it just calls `dispatch(name, input)` when Claude requests a tool.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from tools.youtube_comments_tool import youtube_comments
from tools.youtube_search_tool import youtube_search

log = logging.getLogger(__name__)

# Anthropic tool-use definitions. `input_schema` is JSON Schema.
TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "youtube_search",
        "description": (
            "Search YouTube for real videos matching a query and return each video's title, "
            "channel, view_count, published date and URL. Use this to ground a plan in what is "
            "actually performing on YouTube Shorts for a topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query, e.g. 'rock climbing singing'."},
                "max_results": {
                    "type": "integer",
                    "description": "How many videos to return (default 8).",
                    "default": 8,
                },
                "published_after": {
                    "type": "string",
                    "description": (
                        "Optional RFC3339 UTC timestamp, e.g. '2026-06-09T00:00:00Z'. Only videos "
                        "published after this are returned. Compute it from the user's time window "
                        "(e.g. 'last 7 days') for trend/recency questions."
                    ),
                },
                "order": {
                    "type": "string",
                    "enum": ["relevance", "viewCount", "date", "rating", "title"],
                    "description": "Result ordering. Use 'viewCount' to get the most-watched videos in a window.",
                    "default": "relevance",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "youtube_comments",
        "description": (
            "Fetch the top comments on a specific video (by video_id from a youtube_search result) "
            "to learn what the real audience says about a topic — their language, reactions, pain "
            "points and desires. Returns each comment's author, text and like count. Use after "
            "youtube_search to make a plan authentic to the audience of comparable Shorts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "video_id": {"type": "string", "description": "The video_id from a youtube_search result."},
                "limit": {"type": "integer", "description": "How many top comments to return (default 10).", "default": 10},
            },
            "required": ["video_id"],
        },
    },
]

_DISPATCH = {
    "youtube_search": youtube_search,
    "youtube_comments": youtube_comments,
}


def dispatch(name: str, tool_input: dict[str, Any]) -> str:
    """Run the real Python tool for a Claude tool-use request and return its result as a JSON
    string (the form the SDK expects back in a tool_result block)."""
    fn = _DISPATCH.get(name)
    if fn is None:
        log.warning("Unknown tool requested: %s", name)
        return json.dumps({"error": f"unknown tool {name}"})
    log.info("Executing tool %s(%s)", name, tool_input)
    result = fn(**tool_input)
    return json.dumps(result)
