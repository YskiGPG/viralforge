# ViralForge — Build TODO

Task checklist for building ViralForge. Written to be actionable by Claude Code:
each task states what to do, what "done" looks like, and what it depends on.

**Architecture is fixed** (do not substitute): Anthropic Python SDK directly (no
LangGraph/CrewAI/AutoGen), Skills + Tools pattern, YouTube Data API v3 (video search +
comments), Streamlit frontend. Models: Claude Haiku 4.5 (cheap/fast), Claude Sonnet 4.6
(reasoning). *(Reddit/PRAW was dropped — Reddit now gates API access behind an approval
process; YouTube comments replace it as the audience-signal source.)*

**Settled project decisions** (do not revisit):
- **Output language: English only.** All Skill instructions, generated plans, and demos are
  in English. Do not build bilingual/Chinese output.
- **Primary demo: the climbing/singing example** ("I want to film myself singing while rock
  climbing"). Additional rotating demo examples are a stretch goal only (see 6.3).
- **Quality evaluation: human-reference comparison, NOT LLM-as-a-judge.** Quality is assessed
  by comparing system output to human-authored expert references (see 5.3).

Legend: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Phase 0 — Environment & credentials

- [x] **0.1 Install dependencies.** `pip install -r requirements.txt` in a Python 3.11+ venv.
  *Done when:* imports of `anthropic`, `googleapiclient`, `streamlit`, `dotenv` all succeed.
  *Status:* venv at `.venv/`, all imports verified.
- [x] **0.2 Provision API keys.** Anthropic (console.anthropic.com) and YouTube Data API v3
  (console.cloud.google.com → enable API → API key). *(No Reddit key — dropped, see header.)*
  *Status:* Anthropic + YouTube provided. YouTube comments use the same key.
- [x] **0.3 Fill `.env`.** `cp .env.example .env`, paste real keys.
  *Done when:* `python -c "import sys; sys.path.insert(0,'src'); import config"` runs with no error.
- [x] **0.4 Verify each API.** Run `tests/check_anthropic.py`, `tests/check_youtube.py`,
  `tests/check_youtube_comments.py`.
  *Done when:* all three print their success line and real data.
  *Status:* Anthropic ✅, YouTube search ✅, YouTube comments ✅.
  *Depends on:* 0.3.

---

## Phase 1 — Data Tools

Both tools live in `src/tools/`. Each returns plain Python dicts/lists (no API objects
leaking out), so Skills and the orchestrator stay decoupled from the API SDKs.

- [x] **1.1 Implement `youtube_search_tool.youtube_search`.** *(VERIFIED: 8 dicts, integer view_counts)*
  Wrap YouTube Data API v3 `search().list()`. A `search` call costs 100 quota units
  (10,000/day) and does NOT return view counts — it returns video IDs. To get view counts
  you must make a second `videos().list(part="statistics")` call (cheap, 1 unit) with the
  collected IDs. Implement both: search → collect IDs → fetch statistics → merge.
  *Returns:* `list[dict]` each with `video_id, title, channel, view_count, published_at, url`.
  *Done when:* `youtube_search("rock climbing singing", max_results=8)` returns 8 dicts with
  non-null integer `view_count`.
  *Depends on:* 0.4.
- [x] **1.2 Implement `youtube_comments_tool.youtube_comments`.** *(audience-signal source; replaces Reddit)*
  Wrap YouTube Data API v3 `commentThreads().list()` (1 quota unit) for a given `video_id` from a
  prior `youtube_search` result. Order by relevance; truncate each comment to ~500 chars.
  *Returns:* `list[dict]` each with `author, text, like_count, video_id`.
  *Done when:* `youtube_comments(<a real video_id>, limit=5)` returns dicts with integer `like_count`
  (and degrades to `[]` when comments are disabled).
  *Depends on:* 0.4.
- [x] **1.3 Add basic resilience to both tools.** *(VERIFIED: cache hit on repeat query; comments-disabled degraded to [])*
  return an empty list and log a warning rather than crashing the orchestrator. Add a simple
  in-memory cache (dict keyed by query) so repeated identical searches during one session
  don't burn quota.
  *Done when:* calling the same query twice makes only one real API call (verify via a counter or log).
  *Depends on:* 1.1, 1.2.

---

## Phase 2 — Skills authoring

Each Skill is a folder under `skills/` with a `SKILL.md` (YAML frontmatter: `name`,
`description`, then Markdown instructions). The four folders and placeholder files already
exist — this phase replaces placeholders with real, tested instructions.

Key principle — **progressive disclosure**: only `name` + `description` stay resident in
context; full instructions load only when the orchestrator routes a task to that skill.
So the `description` must be precise enough for routing, and the body must be
self-contained (assume the model reads it cold).

- [x] **2.1 Write `skills/trend_analyst/SKILL.md`.**
  Input: a list of videos (from `youtube_search`) + optionally top comments. Output: a
  structured summary of viral patterns — common title formulas, hook archetypes, what
  separates high-view from low-view videos. Specify the exact output structure in the SKILL.md.
  *Done when:* fed a real `youtube_search` result, the skill produces a structured pattern summary (test via a standalone script before wiring into the orchestrator).
  *Depends on:* 1.1.
- [x] **2.2 Write `skills/hook_writer/SKILL.md`.**
  Input: a video concept + trend insights. Output: a 15-second hook in three beats
  (0–3s / 3–8s / 8–15s), each with on-screen action, spoken/caption line, and the retention
  logic. Define the format explicitly.
  *Done when:* given a concept string, produces all three beats in the specified format.
- [x] **2.3 Write `skills/title_crafter/SKILL.md`.**
  Output: exactly 3 title variants with distinct frames (challenge / series / emotional),
  each with a one-line rationale.
  *Done when:* returns 3 labeled titles for a given concept.
- [x] **2.4 Write `skills/platform_stylist/SKILL.md`.**
  Input: a draft plan. Output: YouTube-Shorts-tuned phrasing + suggested hashtags + a
  recommended posting window. Keep it Shorts-specific (not generic social media).
  *Done when:* returns adjusted copy + tags + post time for a given draft.

---

## Phase 3 — Orchestrator (single-flow first)

Build in `src/orchestrator.py`. This is the Anthropic SDK message loop. **Build the simple
linear version first** (one concept → full pipeline → plan), then add routing in Phase 4.

- [x] **3.1 Define tool schemas for the SDK.** Express `youtube_search` and `youtube_comments`
  as Anthropic tool-use definitions (name, description, JSON input schema). Wire the message
  loop so when Claude requests a tool, the orchestrator runs the real Python function and
  feeds the result back.
  *Done when:* a test prompt that needs YouTube data triggers a real `youtube_search` call and Claude continues with the returned data.
  *Depends on:* 1.1, 1.2.
- [x] **3.2 Implement skill loading via progressive disclosure.** At startup, load only each
  SKILL.md's `name` + `description` into the system prompt. When the orchestrator decides a
  task matches a skill, read that skill's full `SKILL.md` body and inject it. (Write a small
  loader that parses the YAML frontmatter vs. body.)
  *Done when:* a debug log shows only names+descriptions resident initially, and a full body loaded only when that skill is invoked.
  *Depends on:* Phase 2.
- [x] **3.3 Wire the full linear pipeline.** For a complex request, run the sequence:
  youtube_search + youtube_comments → trend_analyst → (hook_writer, title_crafter) →
  platform_stylist → assemble final plan. Use Sonnet 4.6 for reasoning-heavy steps, Haiku 4.5
  for light ones.
  *Done when:* `orchestrator.run("I want to film myself singing while rock climbing")` returns a complete plan (positioning, 3 titles, 15s hook, filming tips, distribution).
  *Depends on:* 3.1, 3.2.
- [x] **3.4 Build the CLI.** A `main`/CLI entry that takes a typed idea and prints the plan.
  This is the **minimum deliverable** — it must run the full flow end to end without the GUI.
  *Done when:* running it from the terminal, typing an idea, and getting a full plan works.
  *Depends on:* 3.3.

---

## Phase 4 — Adaptive routing

The research angle. Not every request needs the full pipeline.

- [x] **4.1 Add intent classification.** Before running the pipeline, have the orchestrator
  classify the request: `complex` (full plan) vs. `simple_followup` (e.g. "rephrase that
  title", "suggest an English song) vs. `knowledge_question`. Use Haiku 4.5 for this — it's
  a cheap routing decision.
  *Done when:* the three example types route to three different paths in a debug log.
  *Depends on:* 3.3.
- [x] **4.2 Implement the single-Skill fast path.** A `simple_followup` loads ONE relevant
  skill and answers directly, skipping data tools and the full pipeline.
  *Done when:* "rephrase that title" returns in noticeably fewer calls / lower latency than a full plan (verify via call count + `time.time()`).
  *Depends on:* 4.1.
- [x] **4.3 Add conversation memory.** Keep prior turns so follow-ups have context
  ("change the song" must know which plan). Hold message history in the session.
  *Done when:* a follow-up correctly references the previous plan without re-stating it.
  *Depends on:* 4.1.

---

## Phase 5 — Evaluation (supports the core architectural claim)

The claim under test: **Skills architecture outperforms a single monolithic prompt on the
same model.** All three axes below feed the final report. No LLM-as-a-judge — quality is
grounded in human references.

- [x] **5.1 Build the single-prompt baseline.** *(VERIFIED: `src/baseline.py`, full plan in 1 call)* One Claude call containing ALL the same
  instructions (the four skills' content concatenated into one monolithic prompt), producing
  the same plan format. This is the control for the A/B comparison.
  *Done when:* the baseline produces a full plan from one idea in a single call.
  *Depends on:* 3.3.
- [x] **5.2 Architecture A/B harness (latency + tokens).** *(VERIFIED: `tests/eval_ab.py` → `docs/eval_results.md`; 2-concept run done, scale with `eval_ab.py all`)* Run both implementations
  (Skills vs. single-prompt) over an identical set of 5–10 test concepts. Measure end-to-end
  latency with `time.time()` and token use by summing `response.usage` across the Skills
  architecture's multiple calls vs. the baseline's single call. Output a comparison table.
  *Done when:* a script prints per-concept latency + token counts for both implementations.
  *Depends on:* 5.1, 4.2.
- [x] **5.3 Output-quality comparison vs. human references.** *(3 concepts across all 3 axes in `docs/eval_quality.md`: climbing, 5 AM challenge (Ali Abdaal), singing challenge (MrBeast) — each with cited creator references and a real CLI-generated plan. Andrew to sanity-check the references/verdicts.)* Collect creator write-ups /
  breakdowns of why specific high-performing Shorts succeeded; where unavailable, pick several
  recognized high-quality videos and write structured descriptions of what makes each work.
  Compare each reference along fixed axes — **positioning, hook pacing, title formula** — and
  judge whether ViralForge's plan for a comparable concept captures the same strategic moves.
  No numeric/LLM scoring; the output is a qualitative match/divergence analysis per axis.
  *Done when:* a doc compares system output to references for ≥3 concepts across all three axes, noting where the plan matches expert moves and where it diverges.
- [x] **5.4 Within-subjects user study.** *(2 creators run, counterbalanced; captured sessions + analysis in `docs/user_study_results.md`. Planning time ~halved, confidence/readiness up, both preferred ViralForge.)* Recruit 2–5 creators. Each produces a plan for one
  idea **unaided**, then a comparable idea **using ViralForge**. Collect planning time,
  perceived quality/actionability, and open-ended feedback. Qualitative only.
  **Important — this evaluates the *planning output*, not published video performance.**
  Creators do NOT film, post, or track real views/engagement. We compare the two *plans*
  (unaided vs. ViralForge-assisted) for the same person; we never attribute real-world video
  metrics to the system. (Real publish-and-measure is out of scope: too noisy — timing,
  follower count, algorithm, thumbnail, luck all dominate — and impossible to attribute to the
  agent with a 2-week, n≤5 study.)
  *Done when:* sessions run with ≥2 creators, each producing both an unaided and an assisted plan, with planning time + qualitative feedback captured for the report. No video is published as part of this study.
  *Depends on:* 3.4 (need a usable CLI/GUI to test with).

---

## Phase 6 — Stretch goals (only if core is done)

- [x] **6.1 Streamlit GUI with streaming.** *(`app.py`: chat UI, token streaming via orchestrator's
  progress hook, live "which Skill/Tool is running" panel. Streaming + boot verified; run `streamlit run app.py`)*
  Build out `app.py`: chat interface that streams the orchestrator's output token by token and
  shows which Skills/Tools are running.
  *Depends on:* 3.4.
- [x] **6.2 "Regenerate / try a different angle" control.** *(button re-runs the last concept with a
  fresh-angle instruction)* A button that re-runs the plan with a variation instruction.
  *Depends on:* 6.1.
- [x] **6.3 2–3 rotating demo examples** *(3 quick-start example buttons in the GUI)* beyond the
  climbing case for the final presentation.

---

## Phase 7 — Deliverables wrap-up

- [ ] **7.1 Final written report.** Cover architecture, the progressive-disclosure mechanism,
  and all three evaluation axes with results.
- [ ] **7.2 Final presentation / demo.** Lead with the climbing example; show the agent
  working live.
- [ ] **7.3 README + repo polish.** Make sure a fresh clone + the Setup steps actually run
  end to end for someone who wasn't there.
