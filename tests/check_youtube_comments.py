"""Minimal check that YouTube comment fetching works (the audience-signal source).

Run:  python tests/check_youtube_comments.py
Expected: prints the top comments on a video found for a sample query.
Note: the search costs 100 quota units; each comment fetch costs 1 — don't loop it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tools.youtube_comments_tool import youtube_comments
from tools.youtube_search_tool import youtube_search

videos = youtube_search("rock climbing singing", max_results=3)
video_id = videos[0]["video_id"]
print(f"Top comments on: {videos[0]['title']}\n")

for c in youtube_comments(video_id, limit=5):
    print(f"{c['like_count']:>6}  {c['text'][:80]}")

print("\n✅ YouTube comments OK")
