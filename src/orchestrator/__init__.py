"""Stage 7 — the orchestrator (Claude Code's role).

Runs the 7-stage funnel for a given run date:
  1. scouts source candidates (parallel)        → list[Candidate]
  2-6. each candidate through quality → valuation → red_team → edge_gate → risk_pm
  7. rank surviving ideas (EV × conviction × asymmetry), build the Briefing, update the watchlist

It logs every stage to `src.store` and hands the `Briefing` to `src.report` for the markdown
deliverable. Implemented across Phases 1–3.
"""
