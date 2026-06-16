# ViralForge

Conversational AI video-planning assistant for YouTube Shorts. User types a natural-language
video idea; the system returns a creative plan (positioning, 3 titles, a 15-second hook,
filming tips, distribution) grounded in real YouTube + Reddit data.

2-person, 2-week university course project. Scope accordingly: simplest thing that works and
demos. Don't add features, abstractions, or robustness the timeline doesn't need.

**Full task list with acceptance criteria: `docs/TODO.md`. Read it before building; respect each
task's `Depends on:` and build toward its `Done when:`.**

## Architecture — do NOT substitute

- Python 3.11+.
- AI framework: **Anthropic Python SDK directly**. NEVER LangGraph, CrewAI, or AutoGen — building
  orchestration on the raw SDK is the point of the project.
- Pattern: **Skills + Tools**. Skills = folders under `skills/` each with a `SKILL.md`. Tools =
  data functions in `src/tools/`. One orchestrator (`src/orchestrator.py`) decides what to invoke.
- Models: use the `MODEL_FAST` / `MODEL_SMART` constants from `src/config.py`. Never hardcode model
  strings elsewhere. (`MODEL_FAST` = Haiku, light tasks; `MODEL_SMART` = Sonnet, reasoning.)
- Data: YouTube Data API v3 + Reddit (PRAW), free tier only. NEVER scrape Xiaohongshu, Instagram,
  or TikTok — ruled out.
- Frontend: Streamlit (stretch). CLI is the minimum deliverable.
- Target: YouTube Shorts only.

## Settled decisions — do NOT revisit

- **Output language: English only.** No bilingual or Chinese output.
- **Primary demo: the climbing/singing example.** Rotating demos are stretch-only.
- **Quality eval: human-reference comparison, NOT LLM-as-a-judge** (`docs/TODO.md` §5.3–5.4). The
  user study evaluates *plans*, not published videos — creators never film or post.

## Progressive disclosure — the core mechanism

The project's thesis is that Skills beat a single monolithic prompt. This depends on progressive
disclosure: only each skill's `name` + `description` stay in context at startup; a skill's full
`SKILL.md` body loads ONLY when the orchestrator routes a task to it.

- **NEVER preload all skill bodies** — that defeats the mechanism the evaluation measures.
- Keep the Skills implementation and the single-prompt baseline (`docs/TODO.md` §5.1) cleanly
  separate so the A/B comparison stays fair.

## Conventions

- Secrets come from `.env` via `src/config.py`. NEVER hardcode keys. NEVER commit `.env` (it's
  gitignored — confirm it's unstaged before every commit).
- Tools return plain Python dicts/lists, NEVER raw SDK/API objects.
- A YouTube `search.list` costs 100 of 10,000 daily units and returns NO view counts — a second
  `videos.list(part="statistics")` call is needed. Cache identical queries within a session.
- Verify current API details from official docs, not memory (limits/signatures change):
  Anthropic https://docs.claude.com/en/api/overview · YouTube
  https://developers.google.com/youtube/v3/docs · PRAW https://praw.readthedocs.io

## How to work here

- Build the simplest version first: single-flow CLI (§3.3–3.4) before routing (§4); routing before
  eval harnesses (§5); core before stretch (§6).
- Leave every `Done when:` verifiable — a small test script or documented command, not just
  plausible-looking code.
- When a change touches a fixed/settled decision above, ask first; don't switch silently.
