"""cli — ViralForge command-line entry. The minimum deliverable.

Usage:
    python src/cli.py "I want to film myself singing while rock climbing"   # one-shot
    python src/cli.py                # interactive chat (supports follow-ups + memory)
    python src/cli.py -v "..."       # -v shows the agent working (routing, skills, tools)

One-shot prints a complete plan and exits. Interactive mode keeps a Session so follow-ups
like "rephrase that title" or "suggest an English song" reuse the previous plan (Phase 4).
"""

from __future__ import annotations

import logging
import sys

import orchestrator


def _interactive() -> int:
    print("🎬 ViralForge — describe a Short idea, then refine it. Type 'quit' to exit.\n")
    session = orchestrator.Session()
    while True:
        try:
            msg = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not msg:
            continue
        if msg.lower() in {"quit", "exit", "q"}:
            return 0
        print("\nThinking…\n")
        print(session.handle(msg))
        print("\n" + "-" * 70 + "\n")


def main(argv: list[str]) -> int:
    verbose = any(a in ("-v", "--verbose") for a in argv)
    args = [a for a in argv if a not in ("-v", "--verbose")]

    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="  · %(message)s",
    )

    if not args:
        return _interactive()

    idea = " ".join(args)
    print("\nPlanning… (this makes several real API + model calls)\n")
    plan = orchestrator.run(idea)
    print("\n" + "=" * 70 + "\n")
    print(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
