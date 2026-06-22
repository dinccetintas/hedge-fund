"""Persistence — git-tracked SQLite + JSON. The track-record dataset and audit log.

Everything a run produces (candidates, per-stage agent outputs, final ideas, watchlist state,
portfolio, trades) is written here, versioned in git. This is sacred: it is both the audit trail
behind the dashboard's traceability and the labeled dataset for Phase-5 calibration/tuning.

Tables (Phase 3 finalizes the schema):
  runs           one row per daily run (id, date, config snapshot, model versions)
  ideas          analyzed opportunities per run (the full Idea object as JSON)
  watchlist      live theses + entry levels + alert state
  portfolio      positions vs targets
  trades         the trade log (realized vs predicted)
"""
