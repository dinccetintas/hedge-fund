"""FMPClient request parsing + the no-look-ahead filter, via a mocked transport."""

from __future__ import annotations

from datetime import date

import httpx

from src.data.fmp_client import FMPClient


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if "stock-screener" in path:
        return httpx.Response(200, json=[
            {"symbol": "AAA", "companyName": "Alpha", "marketCap": 5e9},
        ])
    if "key-metrics" in path:
        return httpx.Response(200, json=[
            {"date": "2026-02-01", "fillingDate": "2026-03-01", "roic": 0.25},  # public, keep
            {"date": "2026-08-01", "fillingDate": "2026-09-01", "roic": 0.30},  # future, drop
        ])
    return httpx.Response(200, json=[])


def _client() -> FMPClient:
    transport = httpx.MockTransport(_handler)
    http = httpx.AsyncClient(transport=transport)
    return FMPClient(api_key="test-key", client=http, use_cache=False)


async def test_screener_returns_rows():
    async with _client() as fmp:
        rows = await fmp.screener(marketCapMoreThan=1e9)
    assert rows and rows[0]["symbol"] == "AAA"


async def test_no_look_ahead_drops_future_filings():
    async with _client() as fmp:
        rows = await fmp.key_metrics("AAA", as_of=date(2026, 6, 1))
    # The row filed 2026-09 (after the 2026-06 decision date) must be excluded.
    assert len(rows) == 1
    assert rows[0]["roic"] == 0.25
