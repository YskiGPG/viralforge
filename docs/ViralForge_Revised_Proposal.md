# ViralForge: A Conversational Multi-Agent Assistant for YouTube Shorts Video Planning

**Group Members:** Andrew Min, Shiqi Yang

## Motivation

Short-form video is now where audience attention and creator income concentrate, yet the distance between having an idea and producing one that performs remains large. Creators must independently work out trends, hooks, titles, and platform-specific style, and existing tools only address fragments of this: analytics dashboards such as VidIQ or TubeBuddy surface raw metrics but leave interpretation to the creator, while generic AI writing tools produce templated copy disconnected from real platform signals. A single prompt to a single model tends to produce generic results for a task this layered. In October 2025, Anthropic released Agent Skills, a framework in which specialized capability modules are discovered and loaded on demand by an orchestrator agent rather than compressed into one monolithic prompt (Anthropic, 2025). Its defining mechanism is *progressive disclosure*: only each skill's short name and description stay resident in the context window, and a skill's full instructions load only when a task matches it. This promises better context efficiency and modularity than a single long prompt, but applications to real creator-facing workflows are still rare. Meanwhile, Xiaohongshu, Instagram, and TikTok have restricted public-discovery access to their APIs, whereas YouTube Data API v3 and Reddit's API remain free and openly accessible (Reddit, 2024). A genuine creator pain point, a fresh architecture, and two free, stable data sources together define the opening we are pursuing.

## Project Type

This is an **Artifact** project — a conversational AI application named *ViralForge*. A user types a natural-language video idea (e.g., *"I want to film myself singing while rock climbing"*) and receives a complete creative plan: core positioning, three title variants, a second-by-second 15-second hook structure, filming recommendations, and a distribution strategy. It is built directly on the Anthropic Python SDK using the Skills + Tools pattern, with an orchestrator agent that routes each request to four reusable Skills (`trend_analyst`, `hook_writer`, `title_crafter`, `platform_stylist`) and two data Tools (`youtube_search_tool` via YouTube Data API v3; `reddit_search_tool` via PRAW). Adaptive routing sends complex requests through the full pipeline and simple follow-ups through a single Skill, avoiding the latency typical of always-on multi-agent demos. The output is delivered through a console interface as the baseline deliverable, with a streaming web UI as a stretch goal.

## Ethical Considerations

Because ViralForge learns patterns from currently high-performing videos, it risks amplifying an existing popularity bias — recommending what already works and nudging creators toward homogeneous, sensational, or clickbait-style framing rather than original work. Our YouTube and Reddit data also reflect whatever demographic and language skew exists in those platforms' popular content, so plans may implicitly favor dominant-culture norms. We will treat the system's output as suggestions with stated reasoning rather than prescriptions, and disclose to users that recommendations are derived from observed engagement patterns, not guarantees.

## Project Deliverables

### Minimum Requirements

- A working **orchestrator agent** built on the Anthropic Python SDK using the Skills + Tools pattern (no third-party orchestration framework).
- The **four Skills** (`trend_analyst`, `hook_writer`, `title_crafter`, `platform_stylist`), each implemented as a folder with a `SKILL.md` file.
- The **two data Tools** (`youtube_search_tool`, `reddit_search_tool`), returning live data within free-tier quotas.
- **Adaptive routing** between the full multi-Skill pipeline and the single-Skill fast path.
- A **console interface** (CLI) that displays the agent's output, sufficient to run and demonstrate the full planning flow end to end.
- **Evaluation across three axes** (detailed in the methodology below): an architecture A/B comparison, an output-quality comparison against human expert references, and a within-subjects user study.

### Stretch Goals

- A **Streamlit web GUI** with streaming output, so users watch the Skills and Tools work in real time.
- A **"regenerate / try a different angle"** control for iterating on a plan.
- Support for **2–3 rotating demo examples** beyond the climbing case for the final presentation.

## Methodology and Evaluation

The architecture is built and evaluated along three axes. We deliberately avoid LLM-as-a-judge scoring; all quality assessment is grounded in human references.

**1. Architecture A/B comparison (latency and token use).** We compare two implementations that produce the same output on the **same Anthropic model** — not against any closed third-party API, which we have no access to and could not measure fairly. The treatment is our **Skills-based architecture** (orchestrator + four Skills loaded via progressive disclosure); the baseline is a **single monolithic prompt** that contains all the same instructions in one call. Running both over an identical set of 5–10 test concepts, we measure end-to-end latency with `time.time()` and token consumption with the `usage` field returned by each API response, summing the Skills architecture's multiple calls for a like-for-like comparison. The research question is whether decomposition's overhead is justified by the gains in context efficiency and controllability.

**2. Output-quality comparison against human expert references.** Rather than auto-scoring, we compare ViralForge's plans to human-authored expert material. We will collect creator write-ups and breakdowns of why specific high-performing Shorts succeeded; where such write-ups are unavailable, we will select several widely recognized high-quality videos and write our own structured descriptions of what makes each work (positioning, hook pacing, title formula). We then compare our system's output for comparable concepts against these references, analyzing qualitatively where the plan captures the same strategic moves an expert would and where it diverges.

**3. Within-subjects user study (qualitative).** We will recruit **2–5 creators**. In a within-subjects design, each participant serves as their own control: every participant produces a plan for a video idea **unaided**, then produces a plan for a comparable idea **using ViralForge**, so we can compare the two conditions for the same person. We will collect qualitative observations — planning time, perceived plan quality and actionability, and open-ended feedback. Given the small sample and time constraints, this is an explicitly **qualitative** comparison; we are not attempting a statistically powered quantitative study.

## Timeline and Work Division

The team pair-programs heavily; the split below marks primary ownership. With a two-week window, evaluation runs concurrently with the back half of development rather than in a dedicated final week.

**Week 1 — Foundation and core pipeline (primary: Shiqi on Tools/data, Andrew on Skills/orchestration)**

- Provision API access: YouTube Data API v3 key, Reddit OAuth credentials, Anthropic API account (Shiqi).
- Implement `youtube_search_tool` and `reddit_search_tool`; confirm they return usable data within free quotas (Shiqi).
- Write the first two Skills, `trend_analyst` and `hook_writer`, with a single-flow CLI proof of concept that takes one idea end to end (Andrew).
- By end of Week 1: one concept can run start to finish through the CLI.

**Week 2 — Completion, baseline, and evaluation (shared)**

- Write the remaining Skills, `title_crafter` and `platform_stylist`, and complete the orchestrator with adaptive routing (Andrew, early week).
- Build the **single-prompt baseline** used in the A/B comparison (Andrew).
- Run the architecture A/B comparison — latency and token use across 5–10 test concepts (Shiqi leads measurement).
- Prepare the human-expert reference set and run the output-quality comparison (Andrew leads analysis).
- Recruit 2–5 creators and run the within-subjects study (Shiqi coordinates recruiting; both run sessions).
- *Stretch, only if core work finishes early:* Streamlit streaming GUI and the regenerate control (Andrew on UI, Shiqi on integration).
- Final presentation and written report (shared, end of Week 2).

## Acknowledgements

We used Anthropic's Claude (Anthropic, 2026) to translate and polish the writing of this proposal from our original Chinese project brief into English, and to clarify our understanding of how the Agent Skills progressive-disclosure mechanism works; no research decisions, methodology choices, or evaluation design were generated by AI. We consulted Anthropic's public documentation for the Agent Skills framework and Python SDK, and the YouTube Data API v3 and Reddit API (PRAW) documentation to confirm rate limits and feasibility within a free-tier budget.

## References

Anthropic. (2025, October 16). *Claude Agent Skills* [Product documentation]. https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview

Reddit. (2024). *Reddit data API terms*. https://www.redditinc.com/policies/data-api-terms
