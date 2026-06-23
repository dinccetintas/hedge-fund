"""Hidden-gem small-cap scout (Waller).

Niche leaders: small-cap, high ROIC (~15–20%), cheap (~10–13x earnings), under-followed. The
small market cap is itself the low-coverage proxy at this stage; deeper scuttlebutt is a later
agent's job.
"""

from __future__ import annotations

from ..schemas import Candidate, ScoutType
from .base import Scout, ScoutContext
from .enrich import enrich_many

MIN_MARKET_CAP = 50_000_000
MAX_MARKET_CAP = 2_000_000_000   # small-cap ceiling
MIN_ROIC = 0.15
MAX_PE = 15.0
MIN_PE = 3.0                      # absurdly low P/E usually signals a value trap / one-off


class HiddenGemScout(Scout):
    scout_type = ScoutType.HIDDEN_GEM

    async def source(self, ctx: ScoutContext, *, limit: int = 25) -> list[Candidate]:
        pool = [
            s for s in ctx.universe
            if MIN_MARKET_CAP <= (s.market_cap or 0) <= MAX_MARKET_CAP
        ]
        # Prefer the larger, more liquid small-caps first for enrichment budget.
        pool.sort(key=lambda s: s.market_cap or 0, reverse=True)
        funds = await enrich_many(
            ctx.fmp, [s.ticker for s in pool], ctx.as_of,
            cap=ctx.enrich_cap, prefetched=ctx.fundamentals,
        )

        out: list[Candidate] = []
        for stock in pool:
            f = funds.get(stock.ticker)
            if f is None or f.roic is None or f.pe is None:
                continue
            if f.roic >= MIN_ROIC and MIN_PE <= f.pe <= MAX_PE:
                reason = (
                    f"Under-covered small-cap leader: ROIC {f.roic:.0%} at P/E {f.pe:.1f}, "
                    f"~${(stock.market_cap or 0) / 1e6:.0f}M cap"
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
