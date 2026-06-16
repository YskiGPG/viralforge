"""tool_registry — exposes the data Tools to Claude as SDK tool-use definitions.

Keeps the Anthropic tool schemas next to the dispatch map, so the orchestrator's message loop
stays small: it just calls `dispatch(name, input)` when Claude requests a tool.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from tools.reddit_search_tool import reddit_search
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
            },
            "required": ["query"],
        },
    },
    {
        "name": "reddit_search",
        "description": (
            "Search Reddit discussions to learn what a real audience says about a topic — their "
            "language, pain points and interests. Returns each post's title, score, comment count "
            "and a snippet. Use to make a plan authentic to the audience."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "subreddit": {
                    "type": "string",
                    "description": "Subreddit to search within, or 'all' (default).",
                    "default": "all",
                },
                "limit": {"type": "integer", "description": "How many posts to return (default 10).", "default": 10},
            },
            "required": ["query"],
        },
    },
]

_DISPATCH = {
    "youtube_search": youtube_search,
    "reddit_search": reddit_search,
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
