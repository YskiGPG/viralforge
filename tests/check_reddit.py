"""Minimal check that the Reddit (PRAW) credentials work.

Run:  python tests/check_reddit.py
Expected: prints 5 hot posts from r/climbing with their scores.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import praw

import config

reddit = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    user_agent=config.REDDIT_USER_AGENT,
)

for post in reddit.subreddit("climbing").hot(limit=5):
    print(f"{post.score:>6}  {post.title}")

print("✅ Reddit OK")
