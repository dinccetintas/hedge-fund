"""Tunable knobs for the funnel: scout weights, IRR hurdle, concentration rules.

These are deliberately centralized so Phase 5 can re-tune them against the track record
without touching agent logic. Values reflect the House View (see CLAUDE.md / METHODOLOGY §2).
"""

from __future__ import annotations

# --- Stage 1: scout weights (balanced composite; re-tune in Phase 5 from realized outcomes) ---
SCOUT_WEIGHTS: dict[str, float] = {
    "thematic": 1.0,        # Citrini/Oguz — second-order beneficiaries. The MU engine.
    "transplant": 1.0,      # Oguz — proven model into an underpenetrated market.
    "quality_compounder": 1.0,  # Slegers/Giuliano/Rijnberk — high ROIC + reinvestment.
    "hidden_gem": 1.0,      # Waller — niche small-cap leaders, low coverage.
    "special_situations": 1.0,  # Walker — spinoffs, forced selling, catalysts.
    "contrarian": 1.0,      # Oguz/Leandro/App Economy — divergence from fundamentals.
}

# --- Stage 3: valuation hurdles ---
IRR_HURDLE_FLOOR = 0.065        # ~6–7% bond-yield-anchored floor; equity must beat debt (MBI).
EXPECTED_RETURN_HURDLE = 0.10   # Slegers-style ≥10% expected-return bar for a buy.
MIN_MARGIN_OF_SAFETY = 0.20     # (intrinsic − price) / intrinsic; minimum to act.

# --- Stage 2: quality gates ---
MIN_QUALITY_SCORE = 6.0         # out of 10; below this, don't advance to sizing.
MIN_ROIC = 0.12                 # sustainable returns on capital floor.
SOFTWARE_MIN_NRR = 1.20         # net revenue retention ≥120% for software (App Economy).
RULE_OF_40_FLOOR = 40.0         # growth% + FCF-margin% for scalers.

# --- Stage 4: forensic red flags (trip => escalate scrutiny / likely kill) ---
RECEIVABLES_TO_SALES_MAX = 0.15  # receivables >15% of sales is a flag.
# (inventory growing faster than sales, peer-anomalous margins, SBC/dilution, leverage, governance)

# --- Stage 6: portfolio construction ---
TARGET_NAMES_MIN = 8
TARGET_NAMES_MAX = 15
MAX_SINGLE_NAME_PCT = 0.20      # cap any one position at 20% of the book at entry.
STARTER_POSITION_PCT = 0.50     # start at ~half target size; add only on validation (Oguz).
MIN_ASYMMETRY_RATIO = 2.0       # upside must be >= 2x downside to size it.

# --- Funnel depth (cost control) ---
# Stages 2–6 are LLM-driven; only the top-N candidates get the full deep dive each run.
DEPTH_LIMIT = 15

# --- Stage 7: ranking ---
# Final score = expected_value * conviction * asymmetry (all normalized). Re-tune in Phase 5.
RANK_WEIGHTS = {"expected_value": 1.0, "conviction": 1.0, "asymmetry": 1.0}
