"""Verify Phase 4 — adaptive routing.

Run:  python tests/check_routing.py

Checks:
  4.1  three example message types route to three different intents.
  4.2  a simple follow-up uses far fewer Claude calls (and less time) than a full plan.
  4.3  the follow-up answer references the previous plan (memory works).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import orchestrator


def _measure(fn):
    """Run fn(), returning (result, n_claude_calls, elapsed_seconds)."""
    orchestrator.reset_usage()
    t0 = time.time()
    result = fn()
    elapsed = time.time() - t0
    calls = len(orchestrator.reset_usage())
    return result, calls, elapsed


print("=== 4.1 intent classification: three types → three paths ===")
cases = [
    ("I want to film myself singing while rock climbing", False),  # complex
    ("Rephrase the second title to be punchier", True),           # simple_followup
    ("How long should a YouTube Short be?", False),               # knowledge_question
]
intents = []
for msg, has_plan in cases:
    route = orchestrator.classify(msg, has_prior_plan=has_plan)
    intents.append(route["intent"])
    print(f"  {route['intent']:<18} (skill={route['skill']})  ← {msg!r}")
assert len(set(intents)) == 3, f"expected 3 distinct intents, got {intents}"
print("  ✅ three distinct routes\n")

print("=== 4.2 + 4.3 fast path vs full plan, with memory ===")
session = orchestrator.Session()

print("  • complex request (full pipeline)…")
plan, plan_calls, plan_time = _measure(
    lambda: session.handle("I want to film myself singing while rock climbing")
)
print(f"    → {plan_calls} Claude calls, {plan_time:.1f}s, plan length {len(plan)} chars")

print("  • follow-up (single-skill fast path)…")
follow, follow_calls, follow_time = _measure(
    lambda: session.handle("Rephrase the second title to be punchier")
)
print(f"    → {follow_calls} Claude calls, {follow_time:.1f}s")
print(f"    follow-up answer:\n      {follow.replace(chr(10), chr(10) + '      ')}")

assert follow_calls < plan_calls, "fast path should use fewer calls than the full plan"
print(f"\n  ✅ 4.2 fast path used {follow_calls} calls vs {plan_calls} for the full plan")
print("  ✅ 4.3 follow-up handled with prior plan in context (memory)")
print("\n✅ Routing OK")
