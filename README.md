# ViralForge 🎬

A conversational AI video-planning assistant for YouTube Shorts. Describe a video idea
in natural language (e.g. *"I want to film myself singing while rock climbing"*) and
ViralForge produces a complete creative plan: core positioning, three title variants, a
second-by-second 15-second hook structure, filming recommendations, and a distribution
strategy — backed by real YouTube video and comment data.

Course project — Northeastern, Summer 2026. Team: Andrew Min, Shiqi Yang.

## Architecture

Built directly on the **Anthropic Python SDK** using the **Skills + Tools** pattern
(no third-party orchestration framework). An orchestrator agent routes each request to
specialized Skills, loading each skill's full instructions only when needed
(*progressive disclosure*).

```
Streamlit chat UI
      │
      ▼
Orchestrator agent  ── decides which Skills + Tools to invoke
      │
  ┌───┴────────────┬──────────────┐
  ▼                ▼              ▼
Skills           Tools          Memory
(how to do it)   (data access)  (convo state)
  │                │
  ├ trend_analyst  ├ youtube_search_tool    (YouTube Data API v3)
  ├ hook_writer    └ youtube_comments_tool  (YouTube comment threads)
  ├ title_crafter
  └ platform_stylist
```

- **Models:** Claude Haiku 4.5 (cheap/fast tasks), Claude Sonnet 4.6 (key reasoning)
- **Data sources:** YouTube Data API v3 — video search + comments (free tier)
- **Frontend:** Streamlit with streaming chat output

## Project layout

```
viralforge/
├── skills/                  # Capability modules (each = a folder + SKILL.md)
│   ├── trend_analyst/
│   ├── hook_writer/
│   ├── title_crafter/
│   └── platform_stylist/
├── src/
│   ├── tools/               # Data-access functions
│   │   ├── youtube_search_tool.py
│   │   └── youtube_comments_tool.py
│   ├── orchestrator.py      # The main agent loop
│   └── config.py            # Loads keys from .env
├── tests/                   # Minimal verification scripts for each API
├── docs/                    # Project briefs and design notes
├── app.py                   # Streamlit entry point
├── requirements.txt
├── .env.example             # Copy to .env and fill in your keys
└── .gitignore
```

## Setup

```bash
# 1. Clone and enter
git clone https://github.com/<your-username>/viralforge.git
cd viralforge

# 2. Create a virtual environment (Python 3.11+)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API keys
cp .env.example .env
# then edit .env with your real keys

# 5. Verify each API works
python tests/check_anthropic.py
python tests/check_youtube.py
python tests/check_youtube_comments.py
```

## Getting API keys

| Service | Where | Cost |
|---|---|---|
| Anthropic | https://console.anthropic.com → API Keys | $5 free credit |
| YouTube Data API v3 | https://console.cloud.google.com → enable API → create API key | Free, no card needed |

See `docs/` for the full project brief.

## Running ViralForge

With your virtual environment active and `.env` filled in:

**CLI** — the minimum deliverable:

```bash
# One-shot: pass an idea, get a full plan, exit
python src/cli.py "I want to film myself singing while rock climbing"

# Interactive: chat and refine, with follow-ups + memory ("rephrase that title")
python src/cli.py

# Add -v to watch the agent work — routing, and which Skills + Tools run
python src/cli.py -v "A 60-second tutorial on making cold brew coffee at home"
```

**Streamlit GUI** — streaming chat with a live "which Skill/Tool is running" panel:

```bash
streamlit run app.py
```

Both make real Anthropic + YouTube API calls, so each run takes a few seconds and uses quota.

## License

MIT — see `LICENSE`.
