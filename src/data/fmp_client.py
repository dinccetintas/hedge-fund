"""FMP (Financial Modeling Prep) client — the primary feed.

Provides the stock **screener** that powers Stage-1 breadth, plus fundamentals, prices, and
earnings. Async (httpx) + retries (tenacity) + on-disk cache + free-tier-friendly throttling.

Targets FMP's current **`/stable`** base (the legacy `/api/v3` base was deprecated on 2025-08-31).
On `/stable`, per-symbol endpoints take the ticker as a `symbol=` query parameter (not a path
segment) and work on free keys; the bulk screener is gated behind a paid plan (Stage-1 breadth is
sourced from Finviz instead). The API key is passed as the `apikey` query parameter.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..settings import settings
from . import cache

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://financialmodelingprep.com/stable"

# Be polite to the free tier (default 250 calls/day, a few req/sec): cap concurrency low so the
# per-candidate fan-out doesn't burst into 429s.
_RATE_LIMIT = asyncio.Semaphore(2)


class FMPError(RuntimeError):
    pass


class FMPClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
        *,
        use_cache: bool = True,
    ):
        self.api_key = api_key or settings.fmp_api_key
        self.base_url = (base_url or settings.fmp_base_url or DEFAULT_BASE_URL).rstrip("/")
        self._client = client
        self._owns_client = client is None
        self.use_cache = use_cache

    async def __aenter__(self) -> FMPClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    # ----------------------------------------------------------------------------------------- #
    # Core request (cache → throttle → retry)
    # ----------------------------------------------------------------------------------------- #
    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        reraise=True,
    )
    async def _request(self, path: str, params: dict[str, Any], *, as_of: str | None) -> Any:
        if self._client is None:
            raise FMPError("FMPClient used outside an `async with` block (no HTTP client).")
        if not self.api_key:
            raise FMPError("No FMP_API_KEY set — add it to .env (see .env.example).")

        if self.use_cache:
            hit = cache.get(path, params, as_of)
            if hit is not None:
                return hit

        url = f"{self.base_url}/{path.lstrip('/')}"
        query = {**params, "apikey": self.api_key}
        async with _RATE_LIMIT:
            resp = await self._client.get(url, params=query)
        if resp.status_code == 429:
            raise httpx.HTTPError("FMP rate limit (429)")  # retried with backoff
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("Error Message"):
            raise FMPError(str(data["Error Message"]))

        if self.use_cache:
            cache.put(path, params, as_of, data)
        return data

    # ----------------------------------------------------------------------------------------- #
    # Stage-1 breadth: the screener
    # ----------------------------------------------------------------------------------------- #
    async def screener(self, *, as_of: date | None = None, **filters: Any) -> list[dict[str, Any]]:
        """Run the stock screener. Common filters: marketCapMoreThan, marketCapLowerThan,
        volumeMoreThan, priceMoreThan, betaMoreThan, sector, industry, exchange,
        isActivelyTrading, isEtf, isFund, country, limit. Returns raw screener rows.
        """
        as_of_key = (as_of or date.today()).isoformat()
        data = await self._request("stock-screener", filters, as_of=as_of_key)
        return data if isinstance(data, list) else []

    # ----------------------------------------------------------------------------------------- #
    # Fundamentals (point-in-time: only statements filed on/before as_of)
    # ----------------------------------------------------------------------------------------- #
    async def profile(self, ticker: str, *, as_of: date | None = None) -> dict[str, Any]:
        data = await self._request("profile", {"symbol": ticker}, as_of=None)
        rows = data if isinstance(data, list) else []
        return rows[0] if rows else {}

    async def _statement(
        self, stmt: str, ticker: str, *, period: str, limit: int, as_of: date | None
    ) -> list[dict[str, Any]]:
        as_of = as_of or date.today()
        data = await self._request(
            stmt,
            {"symbol": ticker, "period": period, "limit": limit},
            as_of=as_of.isoformat(),
        )
        rows = data if isinstance(data, list) else []
        # No look-ahead: drop statements dated after the decision date.
        return [r for r in rows if _row_date(r) <= as_of]

    async def income_statement(
        self, ticker: str, *, period: str = "annual", limit: int = 5, as_of: date | None = None
    ) -> list[dict[str, Any]]:
        return await self._statement(
            "income-statement", ticker, period=period, limit=limit, as_of=as_of
        )

    async def balance_sheet(
        self, ticker: str, *, period: str = "annual", limit: int = 5, as_of: date | None = None
    ) -> list[dict[str, Any]]:
        return await self._statement(
            "balance-sheet-statement", ticker, period=period, limit=limit, as_of=as_of
        )

    async def cash_flow(
        self, ticker: str, *, period: str = "annual", limit: int = 5, as_of: date | None = None
    ) -> list[dict[str, Any]]:
        return await self._statement(
            "cash-flow-statement", ticker, period=period, limit=limit, as_of=as_of
        )

    async def key_metrics(
        self, ticker: str, *, period: str = "annual", limit: int = 5, as_of: date | None = None
    ) -> list[dict[str, Any]]:
        """Key metrics — carries ROIC, ROE, P/E, FCF yield, etc."""
        return await self._statement(
            "key-metrics", ticker, period=period, limit=limit, as_of=as_of
        )

    async def ratios(
        self, ticker: str, *, period: str = "annual", limit: int = 5, as_of: date | None = None
    ) -> list[dict[str, Any]]:
        return await self._statement("ratios", ticker, period=period, limit=limit, as_of=as_of)

    # ----------------------------------------------------------------------------------------- #
    # Prices
    # ----------------------------------------------------------------------------------------- #
    async def prices(
        self, ticker: str, *, as_of: date | None = None, lookback_days: int = 365
    ) -> list[dict[str, Any]]:
        """Daily close prices up to as_of (newest first), for entry-zone / drawdown math.

        Uses `/stable` light EOD history (`{date, price, volume}`); we add a `close` alias so
        downstream consumers that expect OHLCV-style rows keep working.
        """
        as_of = as_of or date.today()
        start = as_of - timedelta(days=lookback_days)
        data = await self._request(
            "historical-price-eod/light",
            {"symbol": ticker, "from": start.isoformat(), "to": as_of.isoformat()},
            as_of=as_of.isoformat(),
        )
        rows = data if isinstance(data, list) else []
        return [{**r, "close": r.get("close", r.get("price"))} for r in rows]

    async def financial_growth(
        self, ticker: str, *, period: str = "annual", limit: int = 5, as_of: date | None = None
    ) -> list[dict[str, Any]]:
        """Growth rates (revenueGrowth, epsgrowth, etc.) for the quality/contrarian scouts."""
        return await self._statement(
            "financial-growth", ticker, period=period, limit=limit, as_of=as_of
        )

    async def earnings_calendar(
        self, *, from_date: date, to_date: date
    ) -> list[dict[str, Any]]:
        data = await self._request(
            "earning_calendar",
            {"from": from_date.isoformat(), "to": to_date.isoformat()},
            as_of=to_date.isoformat(),
        )
        return data if isinstance(data, list) else []

    async def ipo_calendar(self, *, from_date: date, to_date: date) -> list[dict[str, Any]]:
        """Recent/upcoming IPOs — a signal source for the special-situations scout."""
        data = await self._request(
            "ipo_calendar",
            {"from": from_date.isoformat(), "to": to_date.isoformat()},
            as_of=to_date.isoformat(),
        )
        return data if isinstance(data, list) else []


def _row_date(row: dict[str, Any]) -> date:
    """Best-effort statement date for the no-look-ahead filter.

    Prefer the SEC filing/acceptance date when present (that's when the data became public);
    fall back to the fiscal period `date`. Unparseable → date.min so it's never dropped wrongly.
    """
    raw = row.get("fillingDate") or row.get("acceptedDate") or row.get("date")
    if not raw:
        return date.min
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return date.min
