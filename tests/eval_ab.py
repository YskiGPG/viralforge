"""Architecture A/B harness — Skills pipeline vs single-prompt baseline (Phase 5.2).

Runs BOTH implementations over an identical set of concepts and measures, for each:
  - end-to-end latency (time.time())
  - number of Claude calls
  - total tokens (summed response.usage across all calls)

Prints a comparison table and writes it to docs/eval_results.md.

Usage:
    python tests/eval_ab.py            # quick: first 3 concepts
    python tests/eval_ab.py 6          # first 6 concepts
    python tests/eval_ab.py all        # every concept (most representative; costs the most)

This is real API spend: each Skills run is ~8 model calls, each baseline run is 1. Start small.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import baseline
import orchestrator

# A spread of Shorts ideas across genres so the comparison isn't tuned to one niche.
CONCEPTS = [
    "I want to film myself singing while rock climbing",
    "A 60-second tutorial on making cold brew coffee at home",
    "POV: my cat reacts to different sounds",
    "I try a different country's street food every day",
    "Showing my messy desk transform into a clean setup in 30 seconds",
    "Teaching one Spanish phrase that locals actually use",
]


def _measure(run_fn, reset_fn, concept):
    """Run one implementation on one concept; return (latency_s, n_calls, tokens_in, tokens_out)."""
    reset_fn()  # clear any prior usage
    t0 = time.time()
    run_fn(concept)
    latency = time.time() - t0
    usage = reset_fn()
    return latency, len(usage), sum(u["in"] for u in usage), sum(u["out"] for u in usage)


def main(argv):
    if argv and argv[0] == "all":
        concepts = CONCEPTS
    else:
        n = int(argv[0]) if argv else 3
        concepts = CONCEPTS[:n]

    print(f"Running A/B over {len(concepts)} concept(s). This makes real API calls…\n")
    rows = []
    for i, concept in enumerate(concepts, 1):
        print(f"[{i}/{len(concepts)}] {concept!r}")
        print("  · Skills pipeline…", flush=True)
        s_lat, s_calls, s_in, s_out = _measure(orchestrator.run, orchestrator.reset_usage, concept)
        print(f"      {s_lat:5.1f}s, {s_calls} calls, {s_in + s_out} tokens")
        print("  · Single-prompt baseline…", flush=True)
        b_lat, b_calls, b_in, b_out = _measure(baseline.run, baseline.reset_usage, concept)
        print(f"      {b_lat:5.1f}s, {b_calls} calls, {b_in + b_out} tokens\n")
        rows.append((concept, s_lat, s_calls, s_in + s_out, b_lat, b_calls, b_in + b_out))

    # Build a markdown comparison table.
    lines = [
        "# Architecture A/B results (Skills vs single-prompt baseline)",
        "",
        f"Concepts: {len(rows)}. Model: same per config (Skills mixes Haiku+Sonnet by step; "
        "baseline is one Sonnet call). Tokens = input+output summed across all calls.",
        "",
        "| Concept | Skills latency | Skills calls | Skills tokens | Baseline latency | Baseline calls | Baseline tokens |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for c, sl, sc, st, bl, bc, bt in rows:
        short = (c[:40] + "…") if len(c) > 41 else c
        lines.append(f"| {short} | {sl:.1f}s | {sc} | {st} | {bl:.1f}s | {bc} | {bt} |")

    n = len(rows)
    avg = lambda idx: sum(r[idx] for r in rows) / n
    lines += [
        f"| **Average** | **{avg(1):.1f}s** | **{avg(2):.1f}** | **{avg(3):.0f}** "
        f"| **{avg(4):.1f}s** | **{avg(5):.1f}** | **{avg(6):.0f}** |",
        "",
        "## Reading this",
        "",
        "- **Cost of the Skills architecture:** more calls and more tokens (each pipeline step is a "
        "separate call, and progressive disclosure re-sends a skill body as context when invoked).",
        "- **What it buys:** real grounding data (YouTube videos + comments), step-specialized reasoning, and the "
        "adaptive fast path for follow-ups (a single-skill follow-up is ~2 calls, not a full plan).",
        "- Pair this quantitative table with the qualitative quality comparison in `eval_quality.md` "
        "to judge whether the extra cost yields a better *plan*, which is the real claim under test.",
    ]
    out = Path(__file__).resolve().parent.parent / "docs" / "eval_results.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=" * 70)
    print("\n".join(lines[4:]))  # print the table + reading notes
    print("=" * 70)
    print(f"\n✅ Wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
