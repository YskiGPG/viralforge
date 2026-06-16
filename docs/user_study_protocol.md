# Within-subjects user study — protocol & materials (Phase 5.4)

**What this measures:** the quality and speed of the **planning output**, comparing a creator's
**unaided** plan against their **ViralForge-assisted** plan for a comparable idea.

> **Critical scope boundary.** This study evaluates *plans*, NOT published videos. Creators do
> **not** film, post, or track real views/engagement. Real publish-and-measure is out of scope:
> timing, follower count, the algorithm, thumbnail, and luck dominate real-world metrics and make
> attribution to the agent impossible in a 2-week, n ≤ 5 study. We compare the two *plans* for the
> same person; we never attribute video performance to the system.

## Design

- **Within-subjects** (each creator is their own control), **n = 2–5**.
- Each creator produces **two plans**: one **unaided**, one **using ViralForge**, for two
  **comparable-but-different** ideas (so they can't simply copy the first plan into the second).
- **Counterbalance** to blunt learning/order effects: alternate, per creator, both (a) which
  condition comes first (unaided vs assisted) and (b) which idea is paired with which condition.

| Creator | First condition | Idea A (→ condition) | Idea B (→ condition) |
|---|---|---|---|
| C1 | unaided  | A → unaided  | B → assisted |
| C2 | assisted | A → assisted | B → unaided  |
| C3 | unaided  | B → unaided  | A → assisted |
| … | alternate | … | … |

**Idea pairs** (comparable difficulty/genre; pick one pair per creator, or rotate):
- P1: "singing while rock climbing"  ·  "playing guitar while skateboarding"
- P2: "60-second cold brew tutorial"  ·  "60-second iced matcha tutorial"
- P3: "POV: my cat reacts to sounds"  ·  "POV: my dog reacts to words"

## Procedure (per creator, ~30–40 min)

1. **Brief & consent** (2 min). Explain: you'll make two short-video *plans*; nothing is filmed or
   posted; we're studying the planning, not your performance. Confirm OK to record notes/timing.
2. **Condition 1** (≤10 min, timed). Give the assigned idea. *Unaided:* they plan however they
   normally would (notes app, paper). *Assisted:* they use `python src/cli.py` (or the GUI) and may
   refine with follow-ups. **Record planning time** (stop when they say "done").
3. **Quick self-report** (2 min). Two 1–5 self-ratings + one sentence each (see capture sheet).
4. **Condition 2** (≤10 min, timed). The other idea, the other condition. Repeat self-report.
5. **Debrief** (5 min, open-ended). Which plan do they trust more and why? What did the tool get
   right / wrong? Would they use it? Capture verbatim where possible.

## Measures

- **Planning time** per condition (wall-clock, minutes).
- **Perceived quality** (self-report 1–5): "How confident are you this plan would make a strong Short?"
- **Actionability** (self-report 1–5): "How ready do you feel to start filming from this plan?"
- **Open feedback** (qualitative): strengths, gaps, trust, willingness to adopt.

Qualitative only — with n ≤ 5 we report patterns and quotes, not statistics.

## Data-capture sheet (copy one per creator)

```
Creator ID: ____    Date: ____    Idea pair: ____    Order: [unaided-first | assisted-first]

── Condition: UNAIDED — idea: ________________________________
  Planning time (min): ____
  Perceived quality (1–5): ____   one sentence: _________________________________
  Actionability   (1–5): ____   one sentence: _________________________________

── Condition: ASSISTED — idea: ________________________________
  Planning time (min): ____
  Perceived quality (1–5): ____   one sentence: _________________________________
  Actionability   (1–5): ____   one sentence: _________________________________
  Follow-ups used (how many / what): ___________________________________________

── Debrief (verbatim notes)
  Which plan trusted more & why: _______________________________________________
  Tool got right: ______________________________________________________________
  Tool got wrong / missing: ____________________________________________________
  Would adopt? (y/n + why): ____________________________________________________
```

## Analysis (write into the final report)

Per creator, contrast unaided vs assisted on time + both self-ratings, then synthesize across
creators: does ViralForge reduce planning time and/or raise perceived quality/actionability, and
what do the open responses say about *why*? Note dissent and any cases where unaided won. Keep the
plans-not-videos boundary explicit in every claim.
