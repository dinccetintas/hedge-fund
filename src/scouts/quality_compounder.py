"""Quality-compounder scout (Slegers / Giuliano / Rijnberk).

High & sustainable ROIC + organic growth at a reasonable multiple. Screener can't filter on ROIC,
so we pre-filter to investable size, enrich a bounded shortlist, then keep the genuine compounders.
"""

from __future__ import annotations

from ..config import MIN_ROIC
from ..schemas import Candidate, ScoutType
from .base import Scout, ScoutContext
from .enrich import enrich_many

# "Reasonable price" and "organic growth" bars for a compounder.
MAX_PE = 40.0
MIN_REVENUE_GROWTH = 0.07
MIN_MARKET_CAP = 1_000_000_000  # focus on established compounders


class QualityCompounderScout(Scout):
    scout_type = ScoutType.QUALITY_COMPOUNDER

    async def source(self, ctx: ScoutContext, *, limit: int = 25) -> list[Candidate]:
        pool = [
            s for s in ctx.universe
            if (s.market_cap or 0) >= MIN_MARKET_CAP
            and s.sector not in (None, "Financial Services")
        ]
        pool.sort(key=lambda s: s.market_cap or 0, reverse=True)
        funds = await enrich_many(
            ctx.fmp, [s.ticker for s in pool], ctx.as_of, cap=ctx.enrich_cap
        )

        out: list[Candidate] = []
        for stock in pool:
            f = funds.get(stock.ticker)
            if f is None or not f.has_data:
                continue
            roic_ok = f.roic is not None and f.roic >= MIN_ROIC
            growth_ok = f.revenue_growth is not None and f.revenue_growth >= MIN_REVENUE_GROWTH
            price_ok = f.pe is None or 0 < f.pe <= MAX_PE
            if roic_ok and growth_ok and price_ok:
                reason = (
                    f"High-ROIC compounder: ROIC {f.roic:.0%}, revenue growth "
                    f"{f.revenue_growth:.0%}"
                    + (f", P/E {f.pe:.1f}" if f.pe else "")
                )
                out.append(
                    self._candidate(
                        stock,
                        reason,
                        evidence=[self._fundamental_evidence(reason, ctx.as_of, stock.ticker)],
                    )
                )
            if len(out) >= limit:
                break
        return out
