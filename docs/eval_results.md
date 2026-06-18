# Architecture A/B results (Skills vs single-prompt baseline)

Concepts: 6. Model: same per config (Skills mixes Haiku+Sonnet by step; baseline is one Sonnet call). Tokens = input+output summed across all calls.

| Concept | Skills latency | Skills calls | Skills tokens | Baseline latency | Baseline calls | Baseline tokens |
|---|---:|---:|---:|---:|---:|---:|
| I want to film myself singing while rock… | 61.5s | 9 | 19438 | 28.1s | 1 | 3697 |
| A 60-second tutorial on making cold brew… | 58.4s | 9 | 18079 | 30.4s | 1 | 3897 |
| POV: my cat reacts to different sounds | 62.0s | 9 | 21774 | 44.1s | 1 | 4008 |
| I try a different country's street food … | 61.7s | 9 | 21150 | 32.1s | 1 | 3972 |
| Showing my messy desk transform into a c… | 51.4s | 9 | 15323 | 27.3s | 1 | 3775 |
| Teaching one Spanish phrase that locals … | 65.6s | 9 | 22196 | 25.7s | 1 | 3719 |
| **Average** | **60.1s** | **9.0** | **19660** | **31.3s** | **1.0** | **3845** |

## Reading this

- **Cost of the Skills architecture:** more calls and more tokens (each pipeline step is a separate call, and progressive disclosure re-sends a skill body as context when invoked).
- **What it buys:** real grounding data (YouTube videos + comments), step-specialized reasoning, and the adaptive fast path for follow-ups (a single-skill follow-up is ~2 calls, not a full plan).
- Pair this quantitative table with the qualitative quality comparison in `eval_quality.md` to judge whether the extra cost yields a better *plan*, which is the real claim under test.
