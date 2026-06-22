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

from ..data.fmp_client import FMPClient

log = logging.getLogger(__name__)

# Liquid US incl. small-cap (per the approved Phase-1 decision).
US_EXCHANGES = ["NYSE", "NASDAQ", "AMEX"]
MIN_MARKET_CAP = 50_000_000        # $50M floor
MIN_AVG_VOLUME = 100_000           # shares/day — a basic tradability floor


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
