# ViralForge — Team Brief

> Project background and design rationale for team alignment.
> Read this before our first working session.

---

## 1. One-Line Pitch

**ViralForge is a conversational AI video planning assistant. Users describe a video idea in natural language; our system uses an Anthropic Agent SDK + Skills architecture, backed by YouTube and Reddit data, to produce a complete creative plan for YouTube Shorts.**

---

## 2. Course Context

- **Course**: 2026 Summer — Northeastern (AI-related)
- **Immediate deliverable**: 1-page project proposal (PDF upload)
- **Required structure**: Title / Group members (1–3) / Motivation (1 paragraph) / Project type & approach (1 paragraph) / Acknowledgments
- **Project type**: Artifact — a web application
- **Team size**: 2 people
- **Deadline**: Thursday 2pm

---

## 3. What the User Sees

### Step 1 — Landing Page
A minimal chat-style interface. No dropdowns. Just a text box.

```
┌─────────────────────────────────────────────────┐
│              🎬  ViralForge                      │
│        Your AI Video Planning Studio             │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │   Tell me about your video idea...      │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  💡 Try something like:                          │
│  · "I want to film myself singing while          │
│     rock climbing"                               │
│  · "Teaching my grandma to use AI as a series"   │
│  · "My cat learning English, one clip a day"    │
└─────────────────────────────────────────────────┘
```

### Step 2 — User types their idea
> *"I want to film myself climbing while singing Jay Chou's Rice Fragrance"*

### Step 3 — AI works in real time (streaming output)

The user **doesn't** stare at a loading spinner. They watch the system think and produce results token by token:

```
┌─────────────────────────────────────────────────┐
│ 💬 Got it! Extreme activity + unexpected         │
│    behavior = natural virality. Researching...   │
│                                                  │
│ ┌─ 🔍 Trend Scout (running) ──────────────┐     │
│ │ Searching YouTube Shorts for similar     │     │
│ │ content patterns...                      │     │
│ │ ✓ Found 8 reference videos (3.2M views)  │     │
│ └──────────────────────────────────────────┘     │
│                                                  │
│ ┌─ 💭 Community Listener (running) ───────┐     │
│ │ Scanning r/climbing discussions...       │     │
│ │ ✓ Analyzed 15 relevant threads           │     │
│ └──────────────────────────────────────────┘     │
│                                                  │
│ ┌─ ✍️ Plan Generator (running) ───────────┐     │
│ │ Synthesizing insights...                 │     │
│ └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

### Step 4 — Final deliverable

A complete creative plan rendered inline:

```
🎬 YOUR VIDEO PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【Core Positioning】
Not "the singing climber" — instead:
"Using a song to push my climbing limits."
Give the action a purpose. That's why viewers stay.

【3 Title Options】

⭐ Option A (Challenge frame — recommended)
   "Tried to sing 'Rice Fragrance' on a 5.11 route.
    My voice broke by line 3."

○  Option B (Series frame)
   "Climbing Singing Challenge — Day 1"

○  Option C (Emotional frame)
   "What it feels like to sing at 50m up"

【15-Second Hook Structure】
0–3s:  Wide shot, already mid-route
       Caption: "Goal: finish the song before I fall"
3–8s:  Start singing line 1 + cut to ground observers
       reacting in disbelief
8–15s: Voice breaks, hands shake, you laugh
       (This is the retention moment — don't edit out)

【Filming Recommendations】
• Gear: GoPro chest mount + tripod at base + friend
        filming from ground
• Must-capture:
  - Close-up of tense face
  - The voice-crack moment (keep raw audio)
  - Exhausted expression at the top
• Avoid: Polished performance. Imperfection IS the
  content.

【Distribution Strategy】
• Platform: YouTube Shorts
• Tags: #climbing #shorts #challenge #musicchallenge
• Best post window: Friday 8pm PT

【Why This Plan Works】
Based on 8 reference videos analyzed:
✓ Sub-1M-view videos were all too polished
✓ All 1M+ videos shared 3 traits:
  - Clear objective (not just skill display)
  - Visible struggle / imperfection
  - Viewer feels secondhand tension

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 Want to adjust anything?
```

### Step 5 — Conversational follow-ups

Users refine in dialogue. Simple follow-ups are fast (2–3 seconds, single Skill path):

> *"What if I can't film my own face?"*
→ 3 alternatives (free, ~$30, ~$200)

> *"Change the song to something English. Suggestions?"*
→ 5 song suggestions matched to "voice-crack potential"

---

## 4. Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│         FRONTEND: Streamlit Chat UI                  │
│         "I want to film climbing + singing"          │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│   ORCHESTRATOR AGENT (Anthropic Python SDK)          │
│   Responsibilities:                                   │
│   • Parse user intent                                 │
│   • Decide which Skills + Tools to invoke            │
│   • Route simple follow-ups to single-Skill path     │
│   • Stream output back to user                       │
└──────┬──────────────┬────────────────┬──────────────┘
       │              │                │
       ▼              ▼                ▼
  ┌─────────┐    ┌─────────┐     ┌─────────┐
  │ SKILLS  │    │  TOOLS  │     │ MEMORY  │
  │ (How to │    │ (Data   │     │ (Convo  │
  │  do it) │    │ access) │     │ state)  │
  └────┬────┘    └────┬────┘     └─────────┘
       │              │
  ┌────┴────────┐ ┌───┴──────────┐
  │             │ │              │
  ▼             ▼ ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌────────────┐
│ trend_   │ │ hook_    │ │ youtube_     │ │ reddit_    │
│ analyst  │ │ writer   │ │ search_tool  │ │ search_tool│
│ (Skill)  │ │ (Skill)  │ │              │ │            │
└──────────┘ └──────────┘ └──────────────┘ └────────────┘
┌──────────┐ ┌──────────┐
│ title_   │ │ platform_│
│ crafter  │ │ stylist  │
│ (Skill)  │ │ (Skill)  │
└──────────┘ └──────────┘
```

### Key Architectural Decisions

**1. Anthropic SDK, not LangGraph**
- Skills and Tools are first-class concepts in Anthropic's official ecosystem (Skills released October 2025)
- Fewer dependencies, simpler debugging
- Skills more transferable knowledge

**2. Skills as reusable capability modules**

Each Skill is a folder with a `SKILL.md` file plus optional helper scripts:

```
skills/
├── trend_analyst/
│   └── SKILL.md       # "Given a list of videos, extract
│                       #  viral patterns: title formulas,
│                       #  hook types, pacing signals..."
├── hook_writer/
│   └── SKILL.md       # "Generate a 15-second opening hook
│                       #  structure given a video concept..."
├── title_crafter/
│   └── SKILL.md       # "Generate 3 title variants for
│                       #  YouTube Shorts using proven
│                       #  formulas..."
└── platform_stylist/
    └── SKILL.md       # "Adjust copy tone for YouTube
                       #  Shorts: hook-driven, casual,
                       #  retention-focused..."
```

Benefits: reusable, extensible, demoable (add a new SKILL.md live during the final presentation).

**3. Adaptive routing (key research angle)**

Not every user request needs the full multi-Skill pipeline:
- **Complex** ("plan me a video about X") → full pipeline (20–40s with streaming)
- **Simple follow-up** ("rephrase that title") → single Skill, 2–3s
- **Knowledge question** ("what's a good camera for $200?") → single Skill, maybe one Tool call

This adaptive behavior is itself a research contribution — most multi-agent demos always run the full pipeline, which is wasteful.

**4. YouTube + Reddit dual data source**

After researching all major video platforms in 2026:

| Platform | Verdict |
|---|---|
| Xiaohongshu (RED) | ❌ No public API, aggressive anti-scraping, account ban risk |
| Instagram | ❌ 2026 API doesn't support public/hashtag discovery |
| TikTok | ⚠️ Research API requires academic approval, 24h–7d data lag |
| **YouTube** | ✅ Free 10,000 quota units/day, official, stable |
| **Reddit** | ✅ Free 100 req/min, official, great for community discussion |

**YouTube** = hard data (view counts, titles, thumbnails of real top videos)
**Reddit** = soft data (what audiences are actually saying about this kind of content)

---

## 5. Cost Analysis

| Component | Cost |
|---|---|
| Claude API (Haiku 4.5 + Sonnet 4.6) | $5 free credits; estimated total ~$2–4 |
| YouTube Data API v3 | Free (10k units/day) |
| Reddit API | Free (10k requests/month) |
| Streamlit hosting | Free (local) or Streamlit Cloud free tier |
| **Total out-of-pocket** | **$0–5** |

---

## 6. 3-Week Timeline

**Week 1 — Foundation**
- YouTube Data API v3 key (Google Cloud Console)
- Reddit API credentials (OAuth app)
- Anthropic API account ($5 free credits)
- `youtube_search_tool` + `reddit_search_tool`
- First Skill: `trend_analyst`
- Single-flow CLI proof of concept

**Week 2 — Full Pipeline**
- Remaining Skills: `hook_writer`, `title_crafter`, `platform_stylist`
- Orchestrator with adaptive routing
- Streamlit chat UI with streaming
- End-to-end working demo

**Week 3 — Polish + Evaluation**
- Recruit 5–8 real creators for user testing
- Comparison baseline (single long prompt vs. Skills architecture)
- Measure: latency, output quality, token usage
- Final presentation + write-up

---

## 7. Suggested Team Split

**Person A — Backend / Skills**
- Anthropic SDK integration
- Orchestrator logic
- Skills authoring
- Adaptive routing

**Person B — Data / Frontend**
- YouTube + Reddit Tool implementation
- Streamlit UI with streaming
- User testing coordination
- Evaluation framework

(Realistically, pair-program a lot. This is just a starting split.)

---

## 8. Why This Project Is Strong

1. **Real product**, not a toy — solves an actual creator pain point
2. **Cutting-edge architecture** — uses Anthropic Skills (released October 2025), very few projects in the wild
3. **Research depth** — adaptive routing between single-agent and multi-agent paths is an open problem
4. **Demo-friendly** — visualized agent collaboration is compelling
5. **Realistic scope** — 3 weeks, 2 people
6. **Nearly free** — under $5 total

---

## 9. Open Questions for the Team

1. Demo at presentation: only the climbing example, or 2–3 rotating?
2. Output language: English only / Chinese only / bilingual toggle?
3. Should we offer a "regenerate / try different angle" button?
4. How exactly do we score "output quality" in evaluation?
