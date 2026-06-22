"""FMP (Financial Modeling Prep) client — primary feed.

Provides fundamentals, prices, earnings, and the stock **screener** that powers Stage-1 scouts.
Phase 1 implements these against the FMP REST API (httpx + tenacity retries). Until then the
methods raise NotImplementedError so callers fail loudly rather than silently returning stubs.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from ..settings import settings

BASE_URL = "https://financialmodelingprep.com/api/v3"


class FMPClient:
    def __init__(self, api_key: str | None = None, client: httpx.AsyncClient | None = None):
        self.api_key = api_key or settings.fmp_api_key
        self._client = client

    async def screener(self, **filters: Any) -> list[dict[str, Any]]:
        """Run the stock screener (market cap, ROIC, P/E, sector, ...). Stage-1 sourcing.

        TODO(Phase 1): GET /stock-screener with filters; return raw rows.
        """
        raise NotImplementedError("FMP screener — implemented in Phase 1")

    async def fundamentals(self, ticker: str, *, as_of: date) -> dict[str, Any]:
        """Point-in-time fundamentals for a ticker (income, balance, cash flow, ratios).

        TODO(Phase 1): pull statements; filter to filings dated <= as_of (no look-ahead).
        """
        raise NotImplementedError("FMP fundamentals — implemented in Phase 1")

    async def prices(
        self, ticker: str, *, as_of: date, lookback_days: int = 365
    ) -> list[dict[str, Any]]:
        """Daily OHLCV up to as_of (for charts + entry-zone math)."""
        raise NotImplementedError("FMP prices — implemented in Phase 1")
