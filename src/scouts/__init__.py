"""Stage 1 — the scout swarm (6 sourcing patterns, run in parallel, weighted equally).

Each scout scans the universe for one pattern and emits `Candidate`s. The PM at Stage 7 surfaces
the best idea regardless of which scout found it. Scout weights live in `src.config.SCOUT_WEIGHTS`
and are re-tunable in Phase 5 from the track record.

Scouts (see METHODOLOGY §3 Stage 1):
  - thematic            second-order beneficiaries of accelerating secular trends (the MU engine)
  - transplant          proven business model entering an underpenetrated market
  - quality_compounder  high ROIC + reinvestment runway + organic growth at a fair price
  - hidden_gem          niche small-cap leaders, low analyst coverage
  - special_situations  spinoffs, forced selling, busted IPOs/SPACs, catalysts
  - contrarian          quality sold off / ignored; price diverging from north-star fundamentals
"""
