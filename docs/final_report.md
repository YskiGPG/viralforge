# ViralForge: A Skills-and-Tools Agent for YouTube Shorts Planning

**Course project — Northeastern, Summer 2026. Team: Andrew Min, Shiqi Yang.**

## Abstract

ViralForge is a conversational assistant that turns a natural-language video idea into a complete
creative plan for a YouTube Short — positioning, three titles, a second-by-second 15-second hook,
filming tips, and a distribution strategy — grounded in real YouTube data. It is built directly on
the Anthropic Python SDK using a **Skills + Tools** pattern with **progressive disclosure**, rather
than a single monolithic prompt or a third-party orchestration framework. We evaluate the
architecture on three axes: cost (an A/B comparison against a single-prompt baseline), output
quality (a structured comparison against cited human-expert references), and usefulness (a small
within-subjects user study). The Skills pipeline costs roughly 9× the model calls and ~5× the
tokens of the baseline, and what that buys is positioning grounded in what real audiences actually
rewarded — which in several cases diverges, deliberately, from the generic playbook the baseline
defaults to.

## 1. Problem and goal

Short-form creators face a blank-page problem: not a shortage of ideas, but a lack of structure for
turning an idea into something filmable that will hold attention. Generic AI assistants answer this
with plausible-sounding but ungrounded advice ("make a strong hook, use trending sounds"). Our goal
was a planner whose every strategic claim points to a real, currently-performing video, and whose
architecture is itself the object of study: we wanted to test whether composing a few specialized
**Skills** over shared **Tools** produces better plans than concatenating the same instructions into
one large prompt.

## 2. Architecture

### 2.1 Skills + Tools on the raw SDK

The system is built on the Anthropic Python SDK directly — no LangGraph, CrewAI, or AutoGen. This
was a deliberate constraint: building the orchestration ourselves is the point of the project.

- **Tools** are plain data functions in `src/tools/` that return Python dicts (never raw API
  objects), so the rest of the system is decoupled from the data APIs. There are two:
  `youtube_search` (video search + view counts via the YouTube Data API v3) and `youtube_comments`
  (top comments on a video, the audience-signal source).
- **Skills** are prompt modules — each a folder under `skills/` with a `SKILL.md` (YAML
  frontmatter `name` + `description`, then a Markdown instruction body). There are four:
  `trend_analyst`, `hook_writer`, `title_crafter`, and `platform_stylist`.
- **One orchestrator** (`src/orchestrator.py`) runs the Anthropic message loop and decides what to
  invoke.

Two models are used by role (`MODEL_FAST` = Claude Haiku 4.5 for light tasks; `MODEL_SMART` =
Claude Sonnet 4.6 for reasoning), set in one place in `src/config.py`.

### 2.2 Progressive disclosure — the central mechanism

The project's thesis is that Skills beat a single monolithic prompt, and the mechanism that makes
that possible is **progressive disclosure**: at startup only each skill's `name` + `description`
(roughly one line each) are resident in the orchestrator's context. A skill's full instruction body
is loaded **only at the moment the orchestrator routes a task to it** (`skills_loader.load_body`).
This keeps the working context small and focused — each step sees only the instructions it needs —
and it is the variable the A/B evaluation isolates. The single-prompt baseline is kept deliberately
separate (`src/baseline.py`) and uses the *same* skill content concatenated into one prompt, so the
only thing that differs between the two arms is the architecture, not the instructions.

### 2.3 Adaptive routing

Not every message needs the full pipeline. A cheap Haiku classifier first sorts each message into
one of five intents and routes accordingly:

- **complex** → the full planning pipeline.
- **simple_followup** → a single-skill fast path (loads one skill, skips data tools) for tweaks
  like "rephrase that title."
- **evidence_challenge** → re-runs YouTube research and revises the plan citing specific real
  videos, when the user doubts the plan or asks for evidence.
- **trend_query** → a live, time-bounded YouTube search ordered by view count for "what's popular
  now" questions.
- **knowledge_question** → a direct answer, no tools, one call.

A `Session` holds conversation memory (the last plan) so follow-ups have context.

### 2.4 The planning pipeline

For a complex request the orchestrator runs a linear pipeline, mixing models by step:

1. **Research** (Haiku tool loop) — searches YouTube for comparable Shorts, then fetches the top
   comments on the most relevant results.
2. **trend_analyst** (Sonnet) — distills viral patterns (title formulas, hook archetypes, audience
   signal) from the data, citing real videos with view counts.
3. **hook_writer** (Sonnet) and **title_crafter** (Haiku) — produce the 15-second hook and three
   titles, grounded in the trend insights.
4. **Positioning + filming** (Sonnet) — the two sections no single skill owns.
5. **platform_stylist** (Haiku) — a Shorts-specific distribution pass.
6. **Assembly** — skill outputs are stitched deterministically and a clickable **References**
   section of the real source videos is appended, so the plan is visibly grounded.

A behavior policy injected into the answering prompts forbids ungrounded, apologetic, or
work-deflecting output: every strategic claim should point to a real video by title and view count.

### 2.5 A note on the data source

The design originally paired YouTube with Reddit (PRAW) for audience signal. During the project
Reddit moved API credentials behind an approval process, so we replaced Reddit with **YouTube
comments** via `commentThreads.list`. This needs no second credential (it reuses the YouTube key),
and the comments on *comparable videos* are a more on-target audience than a tangential subreddit.
The tools degrade gracefully — a search or comment fetch that fails (e.g. comments disabled) returns
an empty list and the pipeline continues — which we observed live during the evaluation runs.

## 3. Evaluation

The claim under test: **the Skills architecture outperforms a single monolithic prompt on the same
model.** We evaluate on three axes. No LLM-as-a-judge is used; quality is grounded in human
references.

### 3.1 Cost: architecture A/B (5.2)

We ran both implementations over six diverse Short concepts and measured end-to-end latency, number
of Claude calls, and total tokens (`tests/eval_ab.py`, results in `docs/eval_results.md`).

| | Skills pipeline | Single-prompt baseline |
|---|---:|---:|
| Latency (mean) | 60.1 s | 31.3 s |
| Claude calls (mean) | 9.0 | 1.0 |
| Tokens (mean) | 19,660 | 3,845 |

The Skills architecture is unambiguously more expensive: ~9× the calls, ~5× the tokens, ~2× the
wall-clock. This is expected — each pipeline step is a separate call, and progressive disclosure
re-sends a skill body as context when that skill is invoked. The cost is only justified if the
plans are correspondingly better, which is what the next two axes test.

### 3.2 Quality vs. human references (5.3)

For three concepts we placed ViralForge's generated plan beside a cited human-expert reference and
compared along three fixed axes — **positioning, hook pacing, title formula** — recording a
qualitative match/divergence per axis (`docs/eval_quality.md`). The references draw on published
creator breakdowns (e.g. MrBeast via Think Media and Jon Youshaei interviews; Ali Abdaal via Callum
McDonnell's analysis of his content team).

The consistent pattern: **ViralForge reliably reproduces title formulas and hook-pacing structure,
and diverges most on positioning.** The singing-while-climbing concept matched on all three axes.
The "5 AM challenge" (Ali Abdaal) and "last to stop singing" (MrBeast) concepts matched strongly on
title formula and pacing, but pulled away on positioning: for the 5 AM video, ViralForge rejected
the earnest self-improvement framing because its comment data showed that angle gets *mocked*, and
pivoted to an ironic stance; for the singing challenge, it reframed the prize as attainable rather
than spectacular.

Crucially, this divergence is not a failure — it traces to the architecture. The data-grounded
`trend_analyst` step reads real view counts and comments *before* positioning is written, so when
the audience signal contradicts the creator's signature stance, ViralForge follows the data. The
single-prompt baseline, with no live data, has nothing to pull it off the generic archetype.

### 3.3 Usefulness: within-subjects user study (5.4)

Two creators each produced two plans — one unaided, one with ViralForge — for comparable ideas, with
condition order counterbalanced (`docs/user_study_results.md`). This measures the *planning output*,
not published videos; nothing was filmed or posted.

| | Unaided | ViralForge-assisted |
|---|---:|---:|
| Planning time (mean) | 8.5 min | 4.5 min |
| Perceived confidence (mean) | 3.0 | 4.5 |
| Readiness to film (mean) | 2.5 | 4.0 |

Both participants planned roughly twice as fast with ViralForge and rated the assisted plans higher
on confidence and readiness, and both preferred the assisted plan. The effect held in both
counterbalance orders, which argues against a pure practice effect. The participants' own words
locate the benefit in *structure* — a ready hook and shot sequence removing the blank-page problem
("a starting point so I didn't have to stare at a blank page") — while also marking the ceiling
("I wouldn't follow everything exactly… 80% of the way there"). This is a small, qualitative n = 2
study; we report it as a directional pattern, not a statistical result.

## 4. Discussion

Read together, the three axes tell one story. The Skills architecture costs more (3.1), and what
the extra cost buys is grounding: plans whose moves are tied to real, current videos, and
positioning that follows the audience signal even when it departs from a famous creator's playbook
(3.2). Users experience that grounding as a faster, more confident path from idea to filmable plan
(3.3). The single-prompt baseline is cheaper and faster, but structurally cannot do the thing that
makes the output good, because it has no live data and no step dedicated to reading it.

**Limitations.** The A/B is six concepts; the quality comparison is three; the user study is two
participants run by the team. None of these support statistical claims, and the user study measures
self-reported planning quality, not real video performance — a boundary we hold deliberately, since
real-world metrics (timing, follower count, the algorithm, thumbnail, luck) would dominate and could
not be attributed to the agent in a two-week study. The cost figures also reflect one set of model
choices; a different fast/smart split would move them.

## 5. Conclusion

ViralForge demonstrates that a small set of specialized Skills composed over shared Tools, with
progressive disclosure and adaptive routing, produces grounded, usable Short plans — and that the
architecture's measurable cost is repaid in plan quality and user-reported usefulness relative to a
single-prompt baseline on the same model. The most interesting result is qualitative: because the
pipeline reads real audience data before it commits to a stance, it will knowingly diverge from the
generic best-practice answer when the data says to — which is exactly the behavior a planner
grounded in reality should have.
