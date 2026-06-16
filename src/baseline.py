"""baseline — the single-prompt control for the architecture A/B comparison (Phase 5.1).

The claim under test is that the Skills architecture (progressive disclosure + a multi-call
pipeline) beats a single monolithic prompt on the SAME model. This module is the control: it
concatenates the FOUR skills' full instructions into one giant system prompt and produces the
same plan format in a SINGLE Claude call — no progressive disclosure, no pipeline, no tools.

Kept deliberately separate from `orchestrator.py` so the A/B stays fair. It reuses the exact
same skill *content* (loaded from the same SKILL.md files), so the only variable is the
architecture, not the instructions.
"""

from __future__ import annotations

import logging

import anthropic

import config
import skills_loader

log = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Separate usage log so the harness can attribute tokens to the baseline cleanly.
_usage_log: list[dict] = []

# The same four skills the Skills architecture uses — concatenated, not progressively disclosed.
_SKILLS = ["trend_analyst", "hook_writer", "title_crafter", "platform_stylist"]


def _build_system_prompt() -> str:
    """Concatenate all four skill bodies into one monolithic instruction block, plus an output
    spec that matches the Skills pipeline's assembled plan."""
    blocks = []
    for name in _SKILLS:
        blocks.append(f"## Capability: {name}\n\n{skills_loader.load_body(name)}")
    skills_text = "\n\n---\n\n".join(blocks)

    return (
        "You are ViralForge, a YouTube Shorts planning assistant. You have FOUR capabilities, all "
        "described in full below. Use ALL of them, in this order, to turn the user's video idea into "
        "one complete creative plan in a single response.\n\n"
        "Since you have no live data access here, reason from your own knowledge of what performs on "
        "YouTube Shorts for the topic.\n\n"
        f"{skills_text}\n\n"
        "---\n\n"
        "# Output format (produce ALL sections, in this exact order)\n\n"
        "## Positioning\nOne short paragraph: the unique angle and who it's for.\n\n"
        "## Filming tips\n3-5 concrete bullets for actually shooting it.\n\n"
        "## 3 Titles\nThree labeled titles (challenge / series / emotional), each with a one-line rationale.\n\n"
        "## 15-second hook\nThree beats (0-3s / 3-8s / 8-15s), each with on-screen action, the spoken/caption "
        "line, and the retention logic.\n\n"
        "## Distribution\nShorts-tuned description copy, 3-6 hashtags, and a posting window."
    )


def run(user_message: str) -> str:
    """Produce a complete plan in ONE monolithic call. Same output shape as orchestrator.run,
    different architecture."""
    concept = user_message.strip()
    log.info("=== Baseline (single-prompt) run: %r ===", concept)

    resp = _client.messages.create(
        model=config.MODEL_SMART,
        max_tokens=2048,
        system=_build_system_prompt(),
        messages=[{"role": "user", "content": f"Video idea: {concept}"}],
    )
    _usage_log.append(
        {"model": config.MODEL_SMART, "in": resp.usage.input_tokens, "out": resp.usage.output_tokens}
    )
    plan = "".join(b.text for b in resp.content if b.type == "text").strip()

    log.info("Baseline complete. 1 Claude call, tokens in:%d out:%d", resp.usage.input_tokens, resp.usage.output_tokens)
    return f"# ViralForge plan (baseline): {concept}\n\n{plan}"


def reset_usage() -> list[dict]:
    """Return and clear the per-run usage log (used by the Phase 5.2 metrics harness)."""
    snapshot = list(_usage_log)
    _usage_log.clear()
    return snapshot
