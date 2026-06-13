"""Central configuration: loads all API keys from the .env file.

Import the keys you need from here instead of calling os.getenv everywhere.
Fails loudly at import time if a required key is missing, so you find out
immediately rather than mid-request.
"""

import os

from dotenv import load_dotenv

# Reads .env from the project root into environment variables.
load_dotenv()


def _require(name: str) -> str:
    """Fetch an env var, or raise a clear error if it's not set."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Did you copy .env.example to .env and fill it in?"
        )
    return value


# Anthropic
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")

# YouTube
YOUTUBE_API_KEY = _require("YOUTUBE_API_KEY")

# Reddit
REDDIT_CLIENT_ID = _require("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = _require("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = _require("REDDIT_USER_AGENT")

# Model names — kept here so we change them in one place.
MODEL_FAST = "claude-haiku-4-5-20251001"   # cheap/fast tasks
MODEL_SMART = "claude-sonnet-4-6"          # key reasoning
