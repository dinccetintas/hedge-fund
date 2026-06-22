"""Stages 2–6 — the analysis agents (the funnel after sourcing).

Each agent = a Claude call with (a) relevant `methodology/` context, (b) a structured-output
schema from `src.schemas`, (c) cited, dated evidence from FMP + Bigdata.com. Cost-aware routing:
the analysis tier (Sonnet) for Stages 2/4/6, the synthesis tier (Opus) for Stages 3/5.

  Stage 2  quality.py     → QualityAssessment   (Moat / Quality Analyst)
  Stage 3  valuation.py   → Valuation           (Valuation Analyst, reverse-DCF)
  Stage 4  red_team.py    → BearCase            (Red Team / Forensic)
  Stage 5  edge_gate.py   → EdgeVerdict         (Behavioral / Edge)
  Stage 6  risk_pm.py     → SizingPlan          (Risk & Portfolio Manager)
"""
