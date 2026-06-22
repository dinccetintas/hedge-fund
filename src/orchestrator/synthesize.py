"""Stage 7 — synthesis: rank analyzed ideas and assemble the Briefing.

Ranking is deterministic (auditable): rank_score = conviction × asymmetry × (1 + max(IRR, 0)).
This favors high-conviction, asymmetric, positive-IRR ideas — the EV × conviction × asymmetry
intent of the house view — and is re-tunable in Phase 5 from the track record.
"""

from __future__ import annotations

from datetime import date

from ..schemas import Briefing, Idea

ASYMMETRY_CAP = 5.0  # don't let a single huge ratio dominate the ranking


def rank_score(idea: Idea) -> float:
    conviction = idea.sizing.conviction if idea.sizing else 0.0
    asymmetry = idea.bear_case.asymmetry_ratio if idea.bear_case else None
    asymmetry = min(asymmetry or 1.0, ASYMMETRY_CAP)
    irr = idea.valuation.expected_irr_5yr if idea.valuation else None
    return conviction * asymmetry * (1 + max(irr or 0.0, 0.0))


def rank_ideas(ideas: list[Idea]) -> list[Idea]:
    """Set each idea's rank_score and return them sorted best-first."""
    for idea in ideas:
        idea.rank_score = rank_score(idea)
    return sorted(ideas, key=lambda i: i.rank_score or 0.0, reverse=True)


def build_briefing(
    ideas: list[Idea],
    *,
    run_date: date | None = None,
    run_id: str | None = None,
    watchlist_alerts: list[str] | None = None,
    market_regime_note: str | None = None,
) -> Briefing:
    run_date = run_date or date.today()
    ranked = rank_ideas(ideas)
    active_themes = sorted({i.theme for i in ranked if i.theme})
    return Briefing(
        run_date=run_date,
        ideas=ranked,
        watchlist_alerts=watchlist_alerts or [],
        market_regime_note=market_regime_note,
        active_themes=active_themes,
        run_id=run_id,
    )
