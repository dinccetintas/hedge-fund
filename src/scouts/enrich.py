"""Best-effort fundamental enrichment for the quantitative scouts.

The FMP screener returns price/market-cap/volume but not ROIC, P/E, or growth. For those we pull
`key_metrics` + `financial_growth` for a *bounded* shortlist (not the whole universe — that would
blow the free-tier cap). Everything here is defensive: a premium-gated or empty response yields
`None` fields rather than an exception, so scouts can fall back to screener-only heuristics.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import date

from ..data.finviz_client import FinvizRow
from ..data.fmp_client import FMPClient

log = logging.getLogger(__name__)


@dataclass
class Fundamentals:
    ticker: str
    roic: float | None = None
    pe: float | None = None
    revenue_growth: float | None = None
    debt_to_equity: float | None = None
    fcf_yield: float | None = None

    @property
    def has_data(self) -> bool:
        return any(
            v is not None
            for v in (self.roic, self.pe, self.revenue_growth, self.debt_to_equity, self.fcf_yield)
        )


async def fetch_fundamentals(fmp: FMPClient, ticker: str, as_of: date) -> Fundamentals:
    """Pull the latest key metrics + growth for one ticker, swallowing provider errors."""
    f = Fundamentals(ticker=ticker)
    try:
        km = await fmp.key_metrics(ticker, period="annual", limit=1, as_of=as_of)
        if km:
            row = km[0]
            f.roic = row.get("roic")
            f.pe = row.get("peRatio")
            f.debt_to_equity = row.get("debtToEquity")
            f.fcf_yield = row.get("freeCashFlowYield")
    except Exception as e:  # noqa: BLE001 — best-effort; provider/network/premium-gate
        log.debug("key_metrics unavailable for %s: %s", ticker, e)
    try:
        fg = await fmp.financial_growth(ticker, period="annual", limit=1, as_of=as_of)
        if fg:
            f.revenue_growth = fg[0].get("revenueGrowth")
    except Exception as e:  # noqa: BLE001
        log.debug("financial_growth unavailable for %s: %s", ticker, e)
    return f


async def enrich_many(
    fmp: FMPClient,
    tickers: list[str],
    as_of: date,
    *,
    cap: int,
    prefetched: dict[str, Fundamentals] | None = None,
) -> dict[str, Fundamentals]:
    """Enrich up to `cap` tickers concurrently. Returns {ticker: Fundamentals}.

    If `prefetched` is supplied (e.g. fundamentals already pulled from the Finviz screener), those
    are used directly with no per-ticker API calls.
    """
    if prefetched:
        return {t: prefetched[t] for t in tickers if t in prefetched}
    shortlist = tickers[:cap]
    results = await asyncio.gather(*(fetch_fundamentals(fmp, t, as_of) for t in shortlist))
    return {f.ticker: f for f in results}


def fundamentals_from_finviz(rows: list[FinvizRow]) -> dict[str, Fundamentals]:
    """Build the {ticker: Fundamentals} map straight from Finviz screener rows."""
    return {
        r.ticker: Fundamentals(
            ticker=r.ticker,
            roic=r.roic,
            pe=r.pe,
            revenue_growth=r.revenue_growth,
            debt_to_equity=r.debt_to_equity,
            fcf_yield=r.fcf_yield,
        )
        for r in rows
        if r.ticker
    }


def profiles_from_finviz(rows: list[FinvizRow]) -> dict[str, dict]:
    """Synthesize minimal `profile` dicts (price + 52-wk range) so `drawdown_from_high` works.

    Finviz gives distance below the 52-week high directly; we reconstruct a high consistent with it
    so the existing drawdown helper is reusable unchanged.
    """
    out: dict[str, dict] = {}
    for r in rows:
        if not r.ticker or r.price is None or r.pct_below_52w_high is None:
            continue
        high = r.price / (1.0 - r.pct_below_52w_high) if r.pct_below_52w_high < 1.0 else r.price
        out[r.ticker] = {"price": r.price, "range": f"0.01-{high:.4f}"}
    return out


def drawdown_from_high(profile: dict) -> float | None:
    """Percent below the 52-week high, from a profile's `range` ("low-high") and `price`.

    Returns e.g. 0.42 for "42% below its 52-week high", or None if unparseable.
    """
    rng = profile.get("range")
    price = profile.get("price")
    if not rng or price in (None, 0):
        return None
    try:
        _low, high = (float(x) for x in str(rng).split("-"))
    except (ValueError, TypeError):
        return None
    if high <= 0:
        return None
    return max(0.0, (high - float(price)) / high)


async def fetch_profiles(
    fmp: FMPClient,
    tickers: list[str],
    as_of: date,
    *,
    cap: int,
    prefetched: dict[str, dict] | None = None,
) -> dict[str, dict]:
    """Fetch up to `cap` company profiles concurrently (for 52-week-range drawdown).

    If `prefetched` profiles are supplied (e.g. synthesized from Finviz), use them directly.
    """
    if prefetched:
        return {t: prefetched[t] for t in tickers if t in prefetched}
    shortlist = tickers[:cap]

    async def one(t: str) -> tuple[str, dict]:
        try:
            return t, await fmp.profile(t, as_of=as_of)
        except Exception as e:  # noqa: BLE001
            log.debug("profile unavailable for %s: %s", t, e)
            return t, {}

    return dict(await asyncio.gather(*(one(t) for t in shortlist)))
