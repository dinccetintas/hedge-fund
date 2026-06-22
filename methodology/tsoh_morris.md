# TSOH — The Science of Hitting (Alex Morris)

## Core edge
Patience and position-sizing discipline: **"wait for your pitch,"** concentrate in your best
ideas, let winners run, and guard relentlessly against thesis drift.

## Distinctive techniques (encode these)
- **4-variable position-sizing rubric:** 5-year expected return × moat durability × profitability
  predictability × management quality → a conviction-weighted size. This is the system's Stage-6
  sizing model.
- **Top-heavy concentration.** Best ideas carry real weight (top-5 can be >60%).
- **Wait for your pitch.** Don't act without a real edge; cash is a position.
- **Let winners run; beware thesis drift.** Sell on a broken thesis or a consummated catalyst —
  not on price moves alone. Define in advance what would change your mind.
- **Invalidation markers.** Pre-commit to the future data points that would prove the thesis
  wrong, so you notice drift instead of rationalizing it.

## How agents use it
- **Risk/PM agent** implements the 4-variable rubric (`SizingPlan.conviction` + components).
- **Red Team** produces the explicit `invalidation_markers` list (the anti-drift guardrail).
