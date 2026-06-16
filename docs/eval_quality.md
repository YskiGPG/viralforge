# Output-quality comparison vs. human references (Phase 5.3)

**Claim under test (quality axis):** the Skills architecture produces *plans* whose strategic
moves match what expert creators actually do — not just plans that look complete.

**Method.** For each concept we hold a **human-expert reference** beside **ViralForge's plan**
and compare along three fixed axes:

1. **Positioning** — the angle and audience the video stakes out.
2. **Hook pacing** — how the first 15 seconds are structured to hold attention.
3. **Title formula** — the title pattern(s) used to earn the tap.

No numeric scores and no LLM-as-a-judge. The output is a qualitative **match / divergence**
note per axis: where ViralForge captures the expert move, and where it diverges (better, worse,
or merely different). References are descriptions of what recognized high-performing Shorts in
the niche do; where a published creator breakdown exists, cite it and prefer it over a composite.

> How to extend: for each concept, (1) drop in a real creator's breakdown or write a structured
> description of a recognized high-performer, (2) run `python src/cli.py "<comparable idea>"`,
> (3) fill the three-axis table. Done when ≥3 concepts are covered across all three axes.

---

## Concept 1 — Singing while rock climbing  *(worked example)*

**Human-expert reference (composite of music-performance-in-an-unusual-venue Shorts).**
Top performers in this lane treat the stunt as a *performance*, not a novelty: the unusual
venue is the stage, the song's emotional peak is timed to the visual peak, and the hook makes a
human promise ("can she pull it off?") rather than just showing the trick. Titles lean on a
recognizable song/artist for borrowed cultural gravity, or on a stakes question. Hooks open
sound-off with a striking visual + on-screen text, then withhold the payoff to the end.

**ViralForge plan (from `src/cli.py "I want to film myself singing while rock climbing"`).**
- *Positioning:* "music fans first, climbing fans second — the climbing wall is the stage, not
  the subject … time the climax of the song to the hardest move." Targets the music×outdoor overlap.
- *Hook:* 0–3s close-up of chalked hands + 50ft drop + text "she said singing would calm my
  nerves"; 3–8s recognizable song at the crux move; 8–15s mid-lyric, hand peeling off, "wait for it 👀".
- *Titles:* [Challenge] "Can I hit the high note before I fall?"; [Series] "Climbing #1: Taylor
  Swift bridge edition"; [Emotional] "Nobody told me singing makes climbing HARDER".

| Axis | Match / divergence |
|---|---|
| **Positioning** | **Match.** Both frame it as a *performance in an extreme venue*, not a novelty stunt, and both name the crossover audience. ViralForge adds the concrete tactic of syncing the song's peak to the route's crux — the same move experts use. |
| **Hook pacing** | **Match.** Sound-off visual + text in 0–3s, stakes raised by 8s, payoff withheld to the end — textbook Shorts retention structure, and it picks a recognizable song exactly as the reference predicts. |
| **Title formula** | **Match, with breadth.** The reference uses song/artist gravity *or* a stakes question; ViralForge supplies both (Series = Taylor Swift; Challenge = "before I fall") plus an emotional-discovery frame. Divergence is in ViralForge's favor: it offers three distinct, on-pattern frames to A/B. |

**Verdict:** strong match on all three axes; the plan reproduces the expert moves and adds
concrete, on-pattern tactics (peak-syncing, three title frames).

---

## Concept 2 — *(fill in: e.g. "60-second cold brew coffee tutorial")*

**Human-expert reference.** *(Describe what top how-to/recipe Shorts do: positioning as a
fast, foolproof result; hook that shows the finished payoff in 0–3s then rewinds; titles using
a number/“the only way” formula. Cite a real breakdown if available.)*

**ViralForge plan.** *(Run `python src/cli.py "<idea>"` and paste the positioning, hook, titles.)*

| Axis | Match / divergence |
|---|---|
| **Positioning** | *(fill)* |
| **Hook pacing** | *(fill)* |
| **Title formula** | *(fill)* |

---

## Concept 3 — *(fill in: e.g. "POV: my cat reacts to different sounds")*

**Human-expert reference.** *(Describe top pet/POV Shorts moves: relatable-character positioning,
immediate cute/funny payoff in the hook, POV/“nobody:” title formula.)*

**ViralForge plan.** *(Run the CLI and paste output.)*

| Axis | Match / divergence |
|---|---|
| **Positioning** | *(fill)* |
| **Hook pacing** | *(fill)* |
| **Title formula** | *(fill)* |

---

## Cross-concept summary  *(write after ≥3 concepts)*

Summarize the pattern: on which axes does ViralForge reliably match expert moves, and where does
it diverge? Tie back to the architecture — e.g. does the data-grounded trend_analyst step explain
stronger title-formula matches than the single-prompt baseline produces for the same concepts?
