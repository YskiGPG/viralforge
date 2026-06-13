"""Minimal check that the YouTube Data API v3 key works.

Run:  python tests/check_youtube.py
Expected: prints 5 video titles.
Note: one search costs 100 of your 10,000 daily quota units — don't loop it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from googleapiclient.discovery import build

import config

youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)

request = youtube.search().list(
    q="rock climbing singing",
    part="snippet",
    type="video",
    maxResults=5,
)

for item in request.execute()["items"]:
    print(item["snippet"]["title"])

print("✅ YouTube OK")
