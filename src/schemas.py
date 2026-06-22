"""Structured-output schemas — the machine-readable contracts every agent returns.

These are the backbone of two guardrails: **structured output** (auditable scores, not prose)
and **traceability** (every claim carries dated `Evidence`). The dashboard renders purely from
these objects, and the `store/` logs them for the Phase-5 track record.

Nothing here does analysis; these are just the data shapes the funnel passes between stages.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------------------------- #
# Traceability primitives
# --------------------------------------------------------------------------------------------- #
class SourceType(StrEnum):
    FILING = "filing"
    NEWS = "news"
    TRANSCRIPT = "transcript"
    FUNDAMENTAL = "fundamental"  # a metric pulled from FMP/financials
    SENTIMENT = "sentiment"
    OTHER = "other"


class Evidence(BaseModel):
    """A single dated, attributable fact. Every score/claim should point to one or more.

    This is what makes the 'briefing → stock → persona → evidence' trail navigable and
    enforces the no-look-ahead rule (an Evidence dated after the decision date is invalid).
    """

    claim: str = Field(description="The specific fact or data point asserted.")
    source_type: SourceType
    source_name: str = Field(description="e.g. '10-Q Q3 2025', 'Reuters', 'Q2 earnings call'.")
    source_date: date = Field(description="Publication/as-of date. Must precede the decision date.")
    url: str | None = None
    excerpt: str | None = Field(default=None, description="Optional supporting quote.")


# --------------------------------------------------------------------------------------------- #
# Stage 1 — Idea sourcing
# --------------------------------------------------------------------------------------------- #
class ScoutType(StrEnum):
    THEMATIC = "thematic"
    TRANSPLANT = "transplant"
    QUALITY_COMPOUNDER = "quality_compounder"
    HIDDEN_GEM = "hidden_gem"
    SPECIAL_SITUATIONS = "special_situations"
    CONTRARIAN = "contrarian"


class Candidate(BaseModel):
    """A ticker surfaced by a scout, with a one-line reason it was flagged."""

    ticker: str
    company_name: str
    scout: ScoutType
    one_line_reason: str
    theme: str | None = Field(default=None, description="Secular theme, if thematic/second-order.")
    evidence: list[Evidence] = Field(default_factory=list)


# --------------------------------------------------------------------------------------------- #
# Stage 2 — Business quality
# --------------------------------------------------------------------------------------------- #
class MoatDimension(BaseModel):
    """One of Oguz's 5 competitive-advantage axes, scored on strength and direction."""

    name: str  # network_effects | switching_costs | cost_advantage | intangibles_brand | scale
    score: float = Field(ge=0, le=10)
    direction: str = Field(description="widening | stable | eroding")
    rationale: str


class QualityAssessment(BaseModel):
    quality_score: float = Field(ge=0, le=10, description="Slegers-style composite /10.")
    moat: list[MoatDimension]
    roic: float | None = Field(default=None, description="Returns on invested capital (decimal).")
    reinvestment_runway: str | None = Field(
        default=None, description="Can it redeploy at high ROIC?"
    )
    rule_of_40: float | None = None
    net_revenue_retention: float | None = None
    management_note: str | None = Field(
        default=None, description="Owner-operator / capital allocation."
    )
    evidence: list[Evidence] = Field(default_factory=list)


# --------------------------------------------------------------------------------------------- #
# Stage 3 — Valuation
# --------------------------------------------------------------------------------------------- #
class Valuation(BaseModel):
    current_price: float
    buy_below_price: float = Field(description="Price under which the asymmetry is attractive.")
    intrinsic_value: float | None = None
    margin_of_safety: float | None = Field(
        default=None, description="(intrinsic − price)/intrinsic."
    )
    expected_irr_5yr: float | None = Field(default=None, description="Modeled 5-yr IRR (decimal).")
    reverse_dcf_implied_growth: float | None = Field(
        default=None, description="Growth the current price implies (the 'what must be true')."
    )
    achievable_growth_estimate: float | None = Field(
        default=None, description="What the business can realistically deliver."
    )
    multiple_basis: str | None = Field(default=None, description="e.g. EV/FCF, EV/Gross-Profit.")
    evidence: list[Evidence] = Field(default_factory=list)


# --------------------------------------------------------------------------------------------- #
# Stage 4 — Red team / downside
# --------------------------------------------------------------------------------------------- #
class RedFlag(BaseModel):
    name: str
    tripped: bool
    detail: str


class BearCase(BaseModel):
    summary: str
    downside_floor_price: float | None = Field(
        default=None, description="Plausible worst-case price."
    )
    thesis_killers: list[str] = Field(default_factory=list)
    invalidation_markers: list[str] = Field(
        default_factory=list, description="Future data points that would prove the thesis wrong."
    )
    red_flags: list[RedFlag] = Field(default_factory=list)
    asymmetry_ratio: float | None = Field(default=None, description="upside / downside.")
    evidence: list[Evidence] = Field(default_factory=list)


# --------------------------------------------------------------------------------------------- #
# Stage 5 — Edge gate
# --------------------------------------------------------------------------------------------- #
class EdgeVerdict(BaseModel):
    passes: bool
    analytical_edge: str | None = None
    behavioral_edge: str | None = None
    time_arbitrage_rationale: str | None = Field(
        default=None, description="Why the crowd ignores this / why it pays off over years."
    )
    evidence: list[Evidence] = Field(default_factory=list)


# --------------------------------------------------------------------------------------------- #
# Stage 6 — Sizing
# --------------------------------------------------------------------------------------------- #
class SizingPlan(BaseModel):
    """Morris 4-variable rubric → conviction-weighted size + entry plan."""

    conviction: float = Field(ge=0, le=10)
    expected_return_5yr: float | None = None
    moat_durability: float | None = Field(default=None, ge=0, le=10)
    profitability_predictability: float | None = Field(default=None, ge=0, le=10)
    management_quality: float | None = Field(default=None, ge=0, le=10)
    target_weight_pct: float = Field(description="Target % of the book at full size.")
    starter_weight_pct: float = Field(description="Initial (start-small) % of the book.")
    entry_zone_low: float | None = None
    entry_zone_high: float | None = None
    add_on_levels: list[str] = Field(default_factory=list)
    sell_rules: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------------------------- #
# Stage 7 — Synthesis
# --------------------------------------------------------------------------------------------- #
class Idea(BaseModel):
    """A fully-analyzed opportunity — the unit the briefing ranks and the dashboard renders."""

    ticker: str
    company_name: str
    as_of: date
    scout: ScoutType
    thesis_one_line: str
    why_now: str = Field(description="The secular / edge narrative — what changed.")

    quality: QualityAssessment | None = None
    valuation: Valuation | None = None
    bear_case: BearCase | None = None
    edge: EdgeVerdict | None = None
    sizing: SizingPlan | None = None

    rank_score: float | None = Field(default=None, description="EV × conviction × asymmetry.")
    is_new_today: bool = True


class Briefing(BaseModel):
    """The morning deliverable — a ranked list of ideas plus run metadata."""

    run_date: date
    ideas: list[Idea]
    watchlist_alerts: list[str] = Field(default_factory=list)
    market_regime_note: str | None = None
    active_themes: list[str] = Field(default_factory=list)
    run_id: str | None = None
