"""Special-situations scout (Walker).

Two FMP-visible signals in Phase 1:
  - **Recent IPOs** (busted/just-listed) building a public track record — from the IPO calendar.
  - **Forced selling** — extreme drawdowns (≥50% off the 52-week high), the kind that creates
    non-economic sellers.
Spinoffs and index-deletion forced selling need event data the red-team agent will add later.
"""

from __future__ import annotations

from datetime import timedelta

from ..schemas import Candidate, Evidence, ScoutType, SourceType
from .base import Scout, ScoutContext
from .enrich import drawdown_from_high, fetch_profiles

IPO_LOOKBACK_DAYS = 270
FORCED_SELLING_DRAWDOWN = 0.50
MIN_MARKET_CAP = 100_000_000


class SpecialSituationsScout(Scout):
    scout_type = ScoutType.SPECIAL_SITUATIONS

    async def source(self, ctx: ScoutContext, *, limit: int = 25) -> list[Candidate]:
        out: list[Candidate] = []

        # --- Signal 1: recent IPOs that are in our liquid universe -------------------------- #
        try:
            ipos = await ctx.fmp.ipo_calendar(
                from_date=ctx.as_of - timedelta(days=IPO_LOOKBACK_DAYS), to_date=ctx.as_of
            )
        except Exception:  # noqa: BLE001 — endpoint may be premium-gated
            ipos = []
        for ipo in ipos:
            ticker = ipo.get("symbol")
            stock = ctx.by_ticker.get(ticker or "")
            if stock is None:
                continue
            when = ipo.get("date", "recently")
            reason = f"Recent IPO ({when}) now building a public track record"
            ev = Evidence(
                claim=f"{ticker} IPO'd on {when}.",
                source_type=SourceType.OTHER,
                source_name="FMP IPO calendar",
                source_date=ctx.as_of,
            )
            out.append(self._candidate(stock, reason, evidence=[ev]))
            if len(out) >= limit:
                return out

        # --- Signal 2: forced-selling-grade drawdowns --------------------------------------- #
        pool = [s for s in ctx.universe if (s.market_cap or 0) >= MIN_MARKET_CAP]
        pool.sort(key=lambda s: s.market_cap or 0, reverse=True)
        profiles = await fetch_profiles(
            ctx.fmp, [s.ticker for s in pool], ctx.as_of, cap=ctx.enrich_cap
        )
        already = {c.ticker for c in out}
        for stock in pool:
            if stock.ticker in already:
                continue
            dd = drawdown_from_high(profiles.get(stock.ticker, {}))
            if dd is not None and dd >= FORCED_SELLING_DRAWDOWN:
                reason = f"Possible forced selling: down {dd:.0%} from its 52-wk high"
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
