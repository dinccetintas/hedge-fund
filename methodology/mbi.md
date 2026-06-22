# MBI Deep Dives (Mostly Borrowed Ideas — Al-Rezwan)

## Core edge
Deep, valuation-disciplined research on a concentrated set of high-quality compounders, anchored
by **reverse-DCF "what must be true?"** thinking rather than point-target forecasting.

## Distinctive techniques (encode these)
- **Reverse DCF / "what must be true."** Back out the growth and returns the current price
  implies, then ask whether the business can realistically clear that bar. This is the system's
  primary valuation method (Stage 3).
- **Bond-yield-anchored IRR hurdle (~6–7% floor).** Equity must beat the company's own debt /
  the risk-free + spread. If the modeled IRR doesn't clear the floor, it's not asymmetric enough.
- **Moderate growth > hypergrowth.** Hypergrowth attracts capital that competes away returns;
  durable moderate growth at a defensible moat compounds more reliably.
- **Concentration (~10–20 names)** with conviction sizing.

## How agents use it
- **Valuation agent** runs the reverse-DCF, reports `reverse_dcf_implied_growth` vs
  `achievable_growth_estimate`, and applies the IRR floor (`src.config.IRR_HURDLE_FLOOR`).
- **Moat/Quality agent** prefers moderate-durable growth over hype when scoring.
