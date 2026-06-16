"""skills_loader — progressive disclosure for Skills.

The core architectural claim of ViralForge is that Skills beat a monolithic prompt because
only each skill's `name` + `description` stay resident in context at startup; a skill's full
`SKILL.md` body is loaded ONLY when the orchestrator routes a task to it.

This module is the mechanism:
- `load_index()` reads just the frontmatter (name + description) of every skill — cheap, resident.
- `load_body(name)` reads the full instruction body of ONE skill, on demand, and logs that it did.

A SKILL.md is: a `---` fenced YAML-ish frontmatter with `name:` and `description:` lines,
followed by the Markdown instruction body.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def _parse(text: str) -> tuple[dict[str, str], str]:
    """Split a SKILL.md into (frontmatter_dict, body). Frontmatter is between the first
    two `---` lines; everything after is the body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    fm: dict[str, str] = {}
    body_start = len(lines)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body_start = i + 1
            break
        # Only split on the first colon — descriptions contain colons and dashes.
        if ":" in lines[i]:
            key, _, value = lines[i].partition(":")
            fm[key.strip()] = value.strip()

    body = "\n".join(lines[body_start:]).strip()
    return fm, body


def load_index() -> list[dict[str, str]]:
    """Return only `name` + `description` for every skill. This is what stays resident in
    the orchestrator's context — NOT the bodies."""
    index: list[dict[str, str]] = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        fm, _ = _parse(skill_md.read_text(encoding="utf-8"))
        name = fm.get("name") or skill_md.parent.name
        index.append({"name": name, "description": fm.get("description", "")})
    log.info("Resident skill index (name+description only): %s", [s["name"] for s in index])
    return index


def load_body(name: str) -> str:
    """Read the FULL instruction body of one skill, on demand. This is the progressive-
    disclosure step — the body enters context only here, only when invoked."""
    skill_md = SKILLS_DIR / name / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"No skill named {name!r} at {skill_md}")
    _, body = _parse(skill_md.read_text(encoding="utf-8"))
    log.info("Progressive disclosure: loaded full SKILL.md body for %r (%d chars)", name, len(body))
    return body
