"""orchestrator — the main ViralForge agent loop (Phase 3 single-flow + Phase 4 routing).

This is the Anthropic SDK message loop. It:
  1. Researches the concept with the data Tools via SDK tool-use (youtube_search, reddit_search).
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


def _call(model: str, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
    """One focused Claude call. Returns the text. Records usage."""
    resp = _client.messages.create(
        model=model, max_tokens=max_tokens, system=system, messages=messages
    )
    _usage_log.append(
        {"model": model, "in": resp.usage.input_tokens, "out": resp.usage.output_tokens}
    )
    return "".join(block.text for block in resp.content if block.type == "text").strip()


def _research(concept: str) -> dict:
    """Tool-use loop: let Claude (MODEL_FAST) decide what to search, run the real tools, and
    feed results back until it stops. Returns the collected raw tool data, keyed by tool."""
    collected: dict[str, list] = {"youtube_search": [], "reddit_search": []}

    system = (
        "You are the research step of a YouTube Shorts planning assistant. For the given video "
        "idea, gather grounding data: search YouTube for comparable Shorts, and search Reddit for "
        "how the audience talks about the topic. Make at most a few focused tool calls, then stop."
    )
    messages: list[dict] = [{"role": "user", "content": f"Video idea: {concept}"}]

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
            result_json = tool_registry.dispatch(block.name, block.input)
            # Accumulate the structured data so we can feed it straight to trend_analyst.
            parsed = json.loads(result_json)
            if isinstance(parsed, list):
                collected.setdefault(block.name, []).extend(parsed)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result_json}
            )
        messages.append({"role": "user", "content": tool_results})

    log.info(
        "Research gathered: %d youtube, %d reddit",
        len(collected.get("youtube_search", [])),
        len(collected.get("reddit_search", [])),
    )
    return collected


def _run_skill(name: str, model: str, task: str) -> str:
    """Invoke one skill: load its full body NOW (progressive disclosure) and make a focused
    call where that body is the system prompt."""
    body = skills_loader.load_body(name)
    return _call(model, system=body, messages=[{"role": "user", "content": task}])


def _format_data_for_trends(data: dict) -> str:
    """Render collected tool data into a compact text block for trend_analyst."""
    lines = ["YouTube videos (sorted by views):"]
    vids = sorted(data.get("youtube_search", []), key=lambda v: v.get("view_count", 0), reverse=True)
    for v in vids:
        lines.append(f"- {v.get('view_count', 0):>12,} views | {v.get('title', '')} ({v.get('channel', '')})")
    reddit = data.get("reddit_search", [])
    if reddit:
        lines.append("\nReddit discussion:")
        for p in reddit:
            lines.append(f"- [{p.get('score', 0)} pts, {p.get('num_comments', 0)} comments] {p.get('title', '')}")
    return "\n".join(lines) if vids or reddit else "(no data was retrieved)"


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
    data = _research(concept)
    data_block = _format_data_for_trends(data)

    # 2. trend_analyst (reasoning-heavy → MODEL_SMART).
    trends = _run_skill(
        "trend_analyst",
        config.MODEL_SMART,
        f"Topic: {concept}\n\n{data_block}\n\nProduce the viral-pattern summary.",
    )

    # 3. hook_writer (MODEL_SMART) and title_crafter (MODEL_FAST), both grounded in trends.
    hook = _run_skill(
        "hook_writer",
        config.MODEL_SMART,
        f"Concept: {concept}\n\nTrend insights:\n{trends}\n\nWrite the 15-second hook.",
    )
    titles = _run_skill(
        "title_crafter",
        config.MODEL_FAST,
        f"Concept: {concept}\n\nTrend insights:\n{trends}\n\nWrite the 3 titles.",
    )

    # 4. Positioning + filming tips — the two plan sections no single skill owns.
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
    )

    # 5. platform_stylist (MODEL_FAST) — finishing pass for Shorts distribution.
    draft = f"Concept: {concept}\n\n{extras}\n\nTitles:\n{titles}\n\nHook:\n{hook}"
    distribution = _run_skill(
        "platform_stylist",
        config.MODEL_FAST,
        f"Tune this draft plan for YouTube Shorts:\n\n{draft}",
    )

    # 6. Assemble the final plan deterministically (skill outputs kept verbatim).
    plan = (
        f"# ViralForge plan: {concept}\n\n"
        f"{extras}\n\n"
        f"## 3 Titles\n{titles}\n\n"
        f"## 15-second hook\n{hook}\n\n"
        f"## Distribution\n{distribution}\n"
    )

    total_in = sum(u["in"] for u in _usage_log)
    total_out = sum(u["out"] for u in _usage_log)
    log.info("Run complete. %d Claude calls, tokens in:%d out:%d", len(_usage_log), total_in, total_out)

    return plan


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — adaptive routing
# ─────────────────────────────────────────────────────────────────────────────

VALID_INTENTS = {"complex", "simple_followup", "knowledge_question"}


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
        '- "knowledge_question": a general question answerable directly, no data pipeline needed '
        '(e.g. "how long should a Short be?", "how does the algorithm pick videos?").\n\n'
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

    # A follow-up with no prior plan can't refine anything — treat it as a fresh plan.
    if intent == "simple_followup" and not has_prior_plan:
        intent = "complex"

    log.info("Routing decision: intent=%s skill=%s", intent, skill)
    return {"intent": intent, "skill": skill}


def _fast_path(user_message: str, skill: str | None, last_plan: str) -> str:
    """4.2 Single-skill fast path. Loads ONE skill (or none) and answers directly, skipping
    the data tools and the full pipeline — far fewer calls and lower latency than a full plan."""
    plan_context = f"\n\nThe current plan you are refining:\n{last_plan}" if last_plan else ""
    if skill:
        body = skills_loader.load_body(skill)
        system = (
            f"{body}\n\n---\nYou are handling a quick follow-up tweak to an existing plan. Apply your "
            f"skill to JUST what the user asked for — return only the revised piece, not the whole plan."
            f"{plan_context}"
        )
    else:
        system = (
            "You are a YouTube Shorts planning assistant handling a quick follow-up. Answer concisely, "
            f"revising only what the user asked for.{plan_context}"
        )
    return _call(config.MODEL_FAST, system=system, messages=[{"role": "user", "content": user_message}])


def _knowledge_answer(user_message: str) -> str:
    """Direct answer for a general knowledge question — no skills, no tools, one cheap call."""
    system = (
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
        elif intent == "simple_followup":
            answer = _fast_path(user_message, route["skill"], self.last_plan or "")
        else:  # knowledge_question
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
