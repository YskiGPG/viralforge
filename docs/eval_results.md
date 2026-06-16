# Architecture A/B results (Skills vs single-prompt baseline)

Concepts: 2. Model: same per config (Skills mixes Haiku+Sonnet by step; baseline is one Sonnet call). Tokens = input+output summed across all calls.

| Concept | Skills latency | Skills calls | Skills tokens | Baseline latency | Baseline calls | Baseline tokens |
|---|---:|---:|---:|---:|---:|---:|
| I want to film myself singing while rock… | 53.7s | 8 | 10564 | 30.3s | 1 | 3386 |
| A 60-second tutorial on making cold brew… | 53.0s | 9 | 12393 | 27.5s | 1 | 3340 |
| **Average** | **53.4s** | **8.5** | **11478** | **28.9s** | **1.0** | **3363** |

## Reading this

- **Cost of the Skills architecture:** more calls and more tokens (each pipeline step is a separate call, and progressive disclosure re-sends a skill body as context when invoked).
- **What it buys:** real grounding data (YouTube/Reddit), step-specialized reasoning, and the adaptive fast path for follow-ups (a single-skill follow-up is ~2 calls, not a full plan).
- Pair this quantitative table with the qualitative quality comparison in `eval_quality.md` to judge whether the extra cost yields a better *plan*, which is the real claim under test.
