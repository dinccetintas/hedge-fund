"""Broad US universe builder.

One FMP screener call with a liquidity floor → the investable set the scouts work over. We keep
small-cap (that's where under-covered, pre-trend gems live) but drop illiquid micro-caps you
couldn't actually trade. Cached daily via the FMP client.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from ..data.finviz_client import FinvizRow, FinvizScreener
from ..data.fmp_client import FMPClient

log = logging.getLogger(__name__)

# Liquid US incl. small-cap (per the approved Phase-1 decision).
US_EXCHANGES = ["NYSE", "NASDAQ", "AMEX"]
MIN_MARKET_CAP = 50_000_000        # $50M floor
MIN_AVG_VOLUME = 100_000           # shares/day — a basic tradability floor

# Finviz screener filter: US-listed, mid-cap and *under* (≤ ~$10B), with a basic liquidity floor.
# The system's edge is in under-covered small/mid-caps; mega/large-caps are efficiently priced and
# get (correctly) rejected at the behavioral edge gate, so we exclude them at the source.
# (avgvol_o100 == average volume over 100K/day; cap_midunder == market cap ≤ ~$10B.)
FINVIZ_FILTERS = "cap_midunder,sh_avgvol_o100,geo_usa"


@dataclass
class UniverseStock:
    ticker: str
    company_name: str
    market_cap: float | None
    sector: str | None
    industry: str | None
    price: float | None
    volume: float | None
    exchange: str | None
    beta: float | None = None

    @classmethod
    def from_screener_row(cls, row: dict[str, Any]) -> UniverseStock:
        return cls(
            ticker=row.get("symbol", ""),
            company_name=row.get("companyName", ""),
            market_cap=row.get("marketCap"),
            sector=row.get("sector"),
            industry=row.get("industry"),
            price=row.get("price"),
            volume=row.get("volume"),
            exchange=row.get("exchangeShortName") or row.get("exchange"),
            beta=row.get("beta"),
        )


async def build_universe(
    fmp: FMPClient,
    *,
    as_of: date | None = None,
    min_market_cap: float = MIN_MARKET_CAP,
    min_volume: float = MIN_AVG_VOLUME,
    limit: int = 10_000,
) -> list[UniverseStock]:
    """Return the liquid US common-stock universe as of `as_of`.

    Aggregates the screener across the US exchanges, excluding ETFs/funds and inactive names.
    """
    seen: set[str] = set()
    universe: list[UniverseStock] = []
    for exchange in US_EXCHANGES:
        rows = await fmp.screener(
            as_of=as_of,
            marketCapMoreThan=int(min_market_cap),
            volumeMoreThan=int(min_volume),
            exchange=exchange,
            isEtf=False,
            isFund=False,
            isActivelyTrading=True,
            country="US",
            limit=limit,
        )
        for row in rows:
            stock = UniverseStock.from_screener_row(row)
            if stock.ticker and stock.ticker not in seen:
                seen.add(stock.ticker)
                universe.append(stock)

    log.info("Built universe of %d liquid US names (as_of=%s)", len(universe), as_of or date.today())  # noqa: E501
    return universe


def universe_from_finviz(rows: list[FinvizRow]) -> list[UniverseStock]:
    """Map Finviz screener rows into the liquid US universe (dedup by ticker, keep order)."""
    seen: set[str] = set()
    universe: list[UniverseStock] = []
    for r in rows:
        if not r.ticker or r.ticker in seen:
            continue
        seen.add(r.ticker)
        universe.append(
            UniverseStock(
                ticker=r.ticker,
                company_name=r.company,
                market_cap=r.market_cap,
                sector=r.sector,
                industry=r.industry,
                price=r.price,
                volume=r.volume or r.avg_volume,
                exchange=None,  # Finviz custom view does not expose the exchange short-name.
                beta=r.beta,
            )
        )
    return universe


async def build_universe_finviz(
    screener: FinvizScreener,
    *,
    as_of: date | None = None,
    filters: str = FINVIZ_FILTERS,
    max_rows: int = 1000,
) -> tuple[list[UniverseStock], list[FinvizRow]]:
    """Build the universe from Finviz. Returns (universe, raw rows) — rows feed enrichment."""
    rows = await screener.screen(filters=filters, max_rows=max_rows)
    universe = universe_from_finviz(rows)
    log.info("Built Finviz universe of %d names (as_of=%s)", len(universe), as_of or date.today())
    return universe, rows
