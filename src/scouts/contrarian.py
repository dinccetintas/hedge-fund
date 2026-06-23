"""Contrarian / divergence scout (Oguz / Leandro / App Economy).

Quality names sold off hard while the business is still growing — price diverging *below* the
north-star fundamentals. We look for a meaningful drawdown from the 52-week high alongside
still-positive revenue growth (the divergence signal).
"""

from __future__ import annotations

from ..schemas import Candidate, ScoutType
from .base import Scout, ScoutContext
from .enrich import drawdown_from_high, enrich_many, fetch_profiles

MIN_DRAWDOWN = 0.30          # ≥30% below the 52-week high
MIN_MARKET_CAP = 300_000_000  # avoid noise from tiny names
MIN_REVENUE_GROWTH = 0.0     # business still growing despite the sell-off


class ContrarianScout(Scout):
    scout_type = ScoutType.CONTRARIAN

    async def source(self, ctx: ScoutContext, *, limit: int = 25) -> list[Candidate]:
        pool = [s for s in ctx.universe if (s.market_cap or 0) >= MIN_MARKET_CAP]
        pool.sort(key=lambda s: s.market_cap or 0, reverse=True)
        tickers = [s.ticker for s in pool]

        profiles = await fetch_profiles(
            ctx.fmp, tickers, ctx.as_of, cap=ctx.enrich_cap, prefetched=ctx.profiles
        )
        # Only enrich growth for names that actually cleared the drawdown bar (saves calls).
        drawn_down = [
            t for t in tickers
            if (dd := drawdown_from_high(profiles.get(t, {}))) is not None and dd >= MIN_DRAWDOWN
        ]
        funds = await enrich_many(
            ctx.fmp, drawn_down, ctx.as_of, cap=ctx.enrich_cap, prefetched=ctx.fundamentals
        )

        out: list[Candidate] = []
        for stock in pool:
            if stock.ticker not in drawn_down:
                continue
            dd = drawdown_from_high(profiles[stock.ticker]) or 0.0
            f = funds.get(stock.ticker)
            growth = f.revenue_growth if f else None
            # Divergence requires the business to still be growing; if growth is unavailable
            # (free-tier gate), fall back to the drawdown alone but say so in the reason.
            if growth is not None and growth < MIN_REVENUE_GROWTH:
                continue
            reason = (
                f"Down {dd:.0%} from its 52-wk high"
                + (f" while still growing revenue {growth:.0%}" if growth is not None
                   else " (growth unverified — fundamentals gated)")
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
