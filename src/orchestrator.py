"""orchestrator — the main ViralForge agent loop (Phase 3 single-flow + Phase 4 routing).

This is the Anthropic SDK message loop. It:
  1. Researches the concept with the data Tools via SDK tool-use (youtube_search, youtube_comments).
  2. Runs the Skills pipeline using PROGRESSIVE DISCLOSURE — each skill's full body is loaded
     only at the moment it is invoked (see skills_loader).
  3. Assembles a complete creative plan.

Phase 4 adds ADAPTIVE ROUTING on top: a cheap classifier decides whether a message needs the
full pipeline (`complex`), a single-skill fast path (`simple_followup`), or a direct answer
(`knowledge_question`). A `Session` keeps conversation memory so follow-ups have context.

Models follow config: MODEL_SMART (Sonnet) for reasoning-heavy steps, MODEL_FAST (Haiku) for
light ones (classification, follow-ups).
"""

from __future__ import annotations

import datetime
import json
import logging

import anthropic

import config
import skills_loader
import tool_registry

log = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Accumulates token usage across every Claude call in a run, so the Phase 5 A/B harness can
# compare the Skills pipeline (many calls) against the single-prompt baseline (one call).
_usage_log: list[dict] = []

# Optional progress hook for the GUI (Phase 6). A callable taking (kind, data) where kind is one
# of: "step" (a pipeline stage starts), "tool" (a data tool runs), "skill" (a skill body loads),
# "route" (routing decision), "token" (a streamed text delta). None by default → headless/CLI.
_progress = None


def set_progress(callback) -> None:
    """Register a progress callback (or None to clear). Used by the Streamlit GUI to show which
    Skills/Tools are running and to stream tokens. Module-level is fine: Streamlit handles one
    user interaction at a time per session."""
    global _progress
    _progress = callback


def _emit(kind: str, **data) -> None:
    if _progress is not None:
        try:
            _progress(kind, data)
        except Exception:  # noqa: BLE001 — UI hiccups must never break the pipeline
            pass


# Behavior guardrails injected into every conversational/answering system prompt. Encodes the
# "ground in real videos, never bounce work back to the user, no apologetic tone" policy.
BEHAVIOR_RULES = (
    "Behavior rules (always follow):\n"
    "- Do NOT apologize, self-criticize, or narrate what you failed to do. No 'you're right, that's "
    "a gap', no 'I was just guessing', no 'I should have'. Just produce the stronger, grounded "
    "output directly.\n"
    "- When the user questions the plan or asks for references/evidence, do NOT ask them to provide "
    "examples and do NOT offer to 'search together'. Real high-performing videos have already been "
    "retrieved for you; ground your answer in those SPECIFIC videos — name each one with its title "
    "and view count and say what it does well — and revise the plan against them.\n"
    "- Every strategic claim should point to a real video (title + view count), not generic "
    "best-practice. A plan that cites no real videos is a failure."
)


def _call(model: str, system: str, messages: list[dict], max_tokens: int = 1024, label: str | None = None) -> str:
    """One focused Claude call, streamed. Emits each text delta via the progress hook (labelled
    with the current step) and records usage."""
    parts: list[str] = []
    with _client.messages.stream(
        model=model, max_tokens=max_tokens, system=system, messages=messages
    ) as stream:
        for delta in stream.text_stream:
            parts.append(delta)
            _emit("token", text=delta, label=label)
        final = stream.get_final_message()
    _usage_log.append(
        {"model": model, "in": final.usage.input_tokens, "out": final.usage.output_tokens}
    )
    return "".join(parts).strip()


def _run_tool_loop(system: str, user_content: str) -> dict:
    """Generic tool-use loop: Claude (MODEL_FAST) decides what to search, the real tools run, and
    results feed back until it stops. Returns the collected raw tool data, keyed by tool."""
    collected: dict[str, list] = {"youtube_search": [], "youtube_comments": []}
    messages: list[dict] = [{"role": "user", "content": user_content}]

    for _ in range(5):  # hard cap on tool-use turns
        resp = _client.messages.create(
            model=config.MODEL_FAST,
            max_tokens=1024,
            system=system,
            tools=tool_registry.TOOL_DEFS,
            messages=messages,
        )
        _usage_log.append(
            {"model": config.MODEL_FAST, "in": resp.usage.input_tokens, "out": resp.usage.output_tokens}
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            break

        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            _emit("tool", name=block.name, input=block.input)
            result_json = tool_registry.dispatch(block.name, block.input)
            parsed = json.loads(result_json)
            if isinstance(parsed, list):
                collected.setdefault(block.name, []).extend(parsed)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result_json}
            )
        messages.append({"role": "user", "content": tool_results})

    log.info(
        "Tool loop gathered: %d youtube, %d comments",
        len(collected.get("youtube_search", [])),
        len(collected.get("youtube_comments", [])),
    )
    return collected


def _research(concept: str) -> dict:
    """Gather grounding data for a video idea: comparable YouTube Shorts + their top comments."""
    system = (
        "You are the research step of a YouTube Shorts planning assistant. For the given video "
        "idea, gather grounding data: first search YouTube for comparable Shorts with youtube_search, "
        "then fetch the top comments on one or two of the most relevant results with youtube_comments "
        "to learn how the audience talks about the topic. Make at most a few focused tool calls, then stop."
    )
    return _run_tool_loop(system, f"Video idea: {concept}")


def _research_recent(user_message: str) -> dict:
    """Gather data for a TREND/RECENCY question: search YouTube by view count within the user's
    time window. Today's date is injected so Claude can compute publishedAfter itself."""
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    system = (
        f"Today's date is {today} (UTC). The user is asking a TREND or RECENCY question about "
        "YouTube. You DO have live access to the YouTube Data API through the youtube_search tool, "
        "so answer it for real — NEVER say you lack real-time data and NEVER tell the user to use "
        "external tools like TubeBuddy or VidIQ.\n\n"
        "Call youtube_search with:\n"
        "- order='viewCount' (so the most-watched videos come first),\n"
        "- published_after set to an RFC3339 UTC timestamp computed from the requested window "
        "(e.g. 'last 7 days' -> today minus 7 days at 00:00:00Z; 'this month' -> first of the "
        "month; if no window is given, default to the last 30 days),\n"
        "- query set to the topic in the question.\n"
        "Make one or a few focused calls, then stop."
    )
    return _run_tool_loop(system, user_message)


def _run_skill(name: str, model: str, task: str) -> str:
    """Invoke one skill: load its full body NOW (progressive disclosure) and make a focused
    call where that body is the system prompt."""
    _emit("skill", name=name)
    body = skills_loader.load_body(name)
    return _call(model, system=body, messages=[{"role": "user", "content": task}], label=name)


def _human_views(n: int) -> str:
    """Format a view count compactly: 8200000 -> '8.2M', 540000 -> '540K'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _format_data_for_trends(data: dict) -> str:
    """Render collected tool data into a compact text block for trend_analyst. Includes the URL
    so the skill can cite videos as clickable markdown links."""
    lines = ["YouTube videos (sorted by views) — cite these as [title](url):"]
    vids = sorted(data.get("youtube_search", []), key=lambda v: v.get("view_count", 0), reverse=True)
    for v in vids:
        lines.append(
            f"- {v.get('view_count', 0):>12,} views | {v.get('title', '')} "
            f"({v.get('channel', '')}) | {v.get('url', '')}"
        )
    comments = data.get("youtube_comments", [])
    if comments:
        lines.append("\nTop comments on comparable videos (audience signal):")
        for c in comments:
            lines.append(f"- [{c.get('like_count', 0)} likes] {c.get('text', '')}")
    return "\n".join(lines) if vids or comments else "(no data was retrieved)"


def _references_block(data: dict, limit: int = 8) -> str:
    """Build a deterministic, always-present References section of clickable YouTube links from
    the real search results — so the user can open each source video directly."""
    vids = sorted(data.get("youtube_search", []), key=lambda v: v.get("view_count", 0), reverse=True)
    if not vids:
        return ""
    lines = ["## References", "*Real videos this plan is grounded in — click to open:*", ""]
    seen: set[str] = set()
    for v in vids:
        vid = v.get("video_id")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        title = (v.get("title") or "(untitled)").replace("[", "(").replace("]", ")")
        lines.append(
            f"- [{title}]({v.get('url', '')}) — {_human_views(v.get('view_count', 0))} views"
            + (f" · {v['channel']}" if v.get("channel") else "")
        )
        if len(seen) >= limit:
            break
    return "\n".join(lines)


def _full_plan(user_message: str) -> str:
    """Take a natural-language video idea and return a complete creative plan.

    Linear pipeline: research → trend_analyst → (hook_writer + title_crafter) →
    positioning/filming synthesis → platform_stylist → assembled plan.
    """
    concept = user_message.strip()
    log.info("=== ViralForge run: %r ===", concept)

    # Progressive disclosure starts here: only names+descriptions are resident.
    index = skills_loader.load_index()
    log.info("Skills available (resident metadata only): %s", [s["name"] for s in index])

    # 1. Research with the data tools.
    _emit("step", label="Researching YouTube (comparable Shorts + comments)")
    data = _research(concept)
    data_block = _format_data_for_trends(data)

    # 2. trend_analyst (reasoning-heavy → MODEL_SMART).
    _emit("step", label="Analyzing viral patterns (trend_analyst)")
    trends = _run_skill(
        "trend_analyst",
        config.MODEL_SMART,
        f"Topic: {concept}\n\n{data_block}\n\nProduce the viral-pattern summary.",
    )

    # 3. hook_writer (MODEL_SMART) and title_crafter (MODEL_FAST), both grounded in trends.
    _emit("step", label="Writing the 15-second hook (hook_writer)")
    hook = _run_skill(
        "hook_writer",
        config.MODEL_SMART,
        f"Concept: {concept}\n\nTrend insights:\n{trends}\n\nWrite the 15-second hook.",
    )
    _emit("step", label="Crafting 3 titles (title_crafter)")
    titles = _run_skill(
        "title_crafter",
        config.MODEL_FAST,
        f"Concept: {concept}\n\nTrend insights:\n{trends}\n\nWrite the 3 titles.",
    )

    # 4. Positioning + filming tips — the two plan sections no single skill owns.
    _emit("step", label="Writing positioning + filming tips")
    extras = _call(
        config.MODEL_SMART,
        system=(
            "You help plan a YouTube Short. Given the concept and trend insights, write exactly "
            "two short sections in Markdown:\n"
            "## Positioning\nOne short paragraph: the unique angle this video should take to stand "
            "out from what already exists, and who it's for.\n"
            "## Filming tips\n3-5 concrete, practical bullet points for actually shooting it "
            "(framing, pacing, gear, what to capture)."
        ),
        messages=[{"role": "user", "content": f"Concept: {concept}\n\nTrend insights:\n{trends}"}],
        label="positioning",
    )

    # 5. platform_stylist (MODEL_FAST) — finishing pass for Shorts distribution.
    _emit("step", label="Tuning distribution for Shorts (platform_stylist)")
    draft = f"Concept: {concept}\n\n{extras}\n\nTitles:\n{titles}\n\nHook:\n{hook}"
    distribution = _run_skill(
        "platform_stylist",
        config.MODEL_FAST,
        f"Tune this draft plan for YouTube Shorts:\n\n{draft}",
    )

    # 6. Assemble the final plan deterministically (skill outputs kept verbatim). Lead with the
    #    real-video evidence and end with clickable References so the plan is visibly grounded.
    references = _references_block(data)
    plan = (
        f"# ViralForge plan: {concept}\n\n"
        f"## Grounded in real Shorts\n{trends}\n\n"
        f"{extras}\n\n"
        f"## 3 Titles\n{titles}\n\n"
        f"## 15-second hook\n{hook}\n\n"
        f"## Distribution\n{distribution}\n\n"
        f"{references}\n"
    )

    total_in = sum(u["in"] for u in _usage_log)
    total_out = sum(u["out"] for u in _usage_log)
    log.info("Run complete. %d Claude calls, tokens in:%d out:%d", len(_usage_log), total_in, total_out)

    return plan


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — adaptive routing
# ─────────────────────────────────────────────────────────────────────────────

VALID_INTENTS = {"complex", "simple_followup", "knowledge_question", "evidence_challenge", "trend_query"}


def classify(user_message: str, has_prior_plan: bool) -> dict:
    """4.1 Intent classification. A cheap MODEL_FAST call decides the route.

    Returns {"intent": <one of VALID_INTENTS>, "skill": <skill name or None>}.
    The classifier sees ONLY the resident skill index (name+description) — the same
    progressive-disclosure surface — and, for a follow-up, names the single skill to load.
    """
    index = skills_loader.load_index()
    skill_list = "\n".join(f"- {s['name']}: {s['description']}" for s in index)

    system = (
        "You are the router for a YouTube Shorts planning assistant. Classify the user's latest "
        "message into exactly one intent:\n"
        '- "complex": a NEW video idea that needs a full plan (research + hook + titles + distribution).\n'
        '- "simple_followup": a tweak or refinement to the EXISTING plan (e.g. "rephrase that title", '
        '"make the hook punchier", "suggest an English song instead"). Only valid when a prior plan exists.\n'
        '- "evidence_challenge": the user questions the plan\'s quality or grounding, doubts it, calls it '
        'generic, or asks for references/evidence/proof/real examples (e.g. "where are the references?", '
        '"what real videos is this based on?", "this is generic AI slop", "prove it"). Only valid when a '
        'prior plan exists. This route re-searches YouTube and revises the plan against real videos.\n'
        '- "trend_query": a trend, recency, or time-bound question about what is popular/viral now or '
        'in a recent window (e.g. "what\'s trending in fitness shorts", "most popular cover songs in the '
        'last 7 days", "top climbing videos this month"). This route searches YouTube by view count '
        'within the time window. Valid with or without a prior plan.\n'
        '- "knowledge_question": a general, EVERGREEN question answerable directly with no data lookup '
        '(e.g. "how long should a Short be?", "how does the algorithm pick videos?"). If the question is '
        'time-bound or asks what is popular/recent, it is trend_query, not knowledge_question.\n\n'
        f"A prior plan exists in this session: {has_prior_plan}.\n\n"
        "If and only if the intent is simple_followup, also choose the ONE skill best suited to handle "
        "it from this list (else use null):\n"
        f"{skill_list}\n\n"
        'Respond with ONLY a JSON object, no prose: {"intent": "...", "skill": "<name or null>"}'
    )
    raw = _call(
        config.MODEL_FAST,
        system=system,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=80,
        label="_route",  # underscore label → GUI does not stream this internal JSON
    )
    try:
        # Be tolerant of a stray code fence.
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        intent = parsed.get("intent")
        if intent not in VALID_INTENTS:
            raise ValueError(f"bad intent {intent!r}")
        skill = parsed.get("skill")
        skill = skill if skill in {s["name"] for s in index} else None
    except Exception as exc:  # noqa: BLE001 — never let routing crash; default to the safe path
        log.warning("classify failed to parse %r (%s); defaulting to complex", raw, exc)
        intent, skill = "complex", None

    # A follow-up or challenge with no prior plan has nothing to refine — treat it as a fresh plan.
    if intent in {"simple_followup", "evidence_challenge"} and not has_prior_plan:
        intent = "complex"

    log.info("Routing decision: intent=%s skill=%s", intent, skill)
    _emit("route", intent=intent, skill=skill)
    return {"intent": intent, "skill": skill}


def _fast_path(user_message: str, skill: str | None, last_plan: str) -> str:
    """4.2 Single-skill fast path. Loads ONE skill (or none) and answers directly, skipping
    the data tools and the full pipeline — far fewer calls and lower latency than a full plan."""
    plan_context = f"\n\nThe current plan you are refining:\n{last_plan}" if last_plan else ""
    if skill:
        body = skills_loader.load_body(skill)
        system = (
            f"{body}\n\n---\n{BEHAVIOR_RULES}\n\nYou are handling a quick follow-up tweak to an existing "
            f"plan. Apply your skill to JUST what the user asked for — return only the revised piece, "
            f"not the whole plan.{plan_context}"
        )
    else:
        system = (
            f"{BEHAVIOR_RULES}\n\nYou are a YouTube Shorts planning assistant handling a quick follow-up. "
            f"Answer concisely, revising only what the user asked for.{plan_context}"
        )
    return _call(config.MODEL_FAST, system=system, messages=[{"role": "user", "content": user_message}])


def _grounded_revision(user_message: str, last_plan: str) -> str:
    """Evidence-challenge path (2b): the user doubts the plan or wants references. Re-run the
    YouTube research loop with a refined query, then revise the plan citing the SPECIFIC real
    videos retrieved — never bounce the work back to the user."""
    _emit("step", label="Re-searching real videos for evidence")
    # Seed the research with the existing plan + the user's push-back so the query is refined.
    data = _research(f"{last_plan}\n\nUser is challenging this plan: {user_message}")
    data_block = _format_data_for_trends(data)

    _emit("step", label="Revising the plan against real videos")
    system = (
        f"{BEHAVIOR_RULES}\n\n"
        "You are revising a YouTube Shorts plan so it is grounded in REAL videos. You are given the "
        "current plan, the user's challenge, and a list of real YouTube videos with their exact view "
        "counts. Revise the plan so every strategic claim cites specific videos by title and view "
        "count from the data below, and lead with that evidence. Only cite videos that appear in the "
        "data — never invent a title or a number. Return the revised plan, not a discussion of it."
    )
    task = (
        f"Current plan:\n{last_plan}\n\n"
        f"User's challenge: {user_message}\n\n"
        f"Real videos retrieved (cite these by title + view count):\n{data_block}"
    )
    revised = _call(config.MODEL_SMART, system=system, messages=[{"role": "user", "content": task}], label="revision")
    references = _references_block(data)
    return f"{revised}\n\n{references}" if references else revised


def _trend_query(user_message: str) -> str:
    """Trend/recency path: a time-bound question ('most popular X in the last 7 days') triggers a
    real YouTube search (order=viewCount + published_after window), then a grounded answer with
    clickable references. Never deflects with 'I lack real-time data' or external-tool suggestions."""
    _emit("step", label="Searching recent top videos on YouTube")
    data = _research_recent(user_message)
    data_block = _format_data_for_trends(data)

    _emit("step", label="Answering from real videos")
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    system = (
        f"{BEHAVIOR_RULES}\n\n"
        f"Today is {today} (UTC). Answer the user's trend/recency question using ONLY the real "
        "YouTube videos below — they were just fetched live from the YouTube Data API, ordered by "
        "views, within the requested time window. Cite specific videos as [title](url) with their "
        "view counts. Do NOT claim you lack real-time data and do NOT suggest external tools "
        "(TubeBuddy, VidIQ, etc.) — you already have the data. If the list is empty, say the search "
        "returned nothing for that window and suggest widening it."
    )
    answer = _call(
        config.MODEL_SMART,
        system=system,
        messages=[{"role": "user", "content": f"Question: {user_message}\n\nReal videos:\n{data_block}"}],
        label="trend",
    )
    references = _references_block(data)
    return f"{answer}\n\n{references}" if references else answer


def _knowledge_answer(user_message: str) -> str:
    """Direct answer for a general knowledge question — no skills, no tools, one cheap call."""
    system = (
        f"{BEHAVIOR_RULES}\n\n"
        "You are a knowledgeable YouTube Shorts strategist. Answer the user's question directly and "
        "concisely. No need to produce a full video plan."
    )
    return _call(config.MODEL_FAST, system=system, messages=[{"role": "user", "content": user_message}])


class Session:
    """4.3 Conversation memory. Holds the last produced plan so follow-ups have context.

    Call `handle(message)` for each user turn; it routes via `classify` and dispatches to the
    full pipeline, the fast path, or a direct answer.
    """

    def __init__(self) -> None:
        self.last_plan: str | None = None
        self.turns: list[dict] = []  # [{"role": "user"/"assistant", "content": str}, ...]

    def handle(self, user_message: str) -> str:
        route = classify(user_message, has_prior_plan=self.last_plan is not None)
        intent = route["intent"]

        if intent == "complex":
            answer = _full_plan(user_message)
            self.last_plan = answer
        elif intent == "trend_query":
            _emit("step", label="Trend query → live YouTube search")
            answer = _trend_query(user_message)
        elif intent == "evidence_challenge":
            answer = _grounded_revision(user_message, self.last_plan or "")
            self.last_plan = answer  # the grounded revision becomes the new working plan
        elif intent == "simple_followup":
            _emit("step", label=f"Fast path → {route['skill'] or 'direct'}")
            answer = _fast_path(user_message, route["skill"], self.last_plan or "")
        else:  # knowledge_question
            _emit("step", label="Answering directly")
            answer = _knowledge_answer(user_message)

        self.turns.append({"role": "user", "content": user_message})
        self.turns.append({"role": "assistant", "content": answer})
        return answer


def run(user_message: str) -> str:
    """One-shot entry: route a single message through a fresh session. Back-compatible with the
    Phase 3 CLI and the Phase 5 baseline harness."""
    return Session().handle(user_message)


def reset_usage() -> list[dict]:
    """Return and clear the per-run usage log (used by the Phase 5 metrics harness)."""
    snapshot = list(_usage_log)
    _usage_log.clear()
    return snapshot
