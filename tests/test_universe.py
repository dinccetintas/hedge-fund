"""Universe builder dedupes across exchanges and maps screener rows."""

from __future__ import annotations

from datetime import date

from src.universe.build import build_universe
from tests.conftest import FakeFMP


async def test_build_universe_dedupes_and_maps():
    rows = [
        {"symbol": "AAA", "companyName": "Alpha", "marketCap": 5e9, "sector": "Technology",
         "price": 100.0, "volume": 2_000_000, "exchangeShortName": "NASDAQ"},
        {"symbol": "BBB", "companyName": "Beta", "marketCap": 1e9, "sector": "Industrials",
         "price": 50.0, "volume": 500_000, "exchangeShortName": "NYSE"},
    ]
    # FakeFMP.screener returns the same rows for each of the 3 exchange calls → must dedupe.
    fmp = FakeFMP(screener_rows=rows)
    universe = await build_universe(fmp, as_of=date(2026, 6, 1))

    assert {s.ticker for s in universe} == {"AAA", "BBB"}
    alpha = next(s for s in universe if s.ticker == "AAA")
    assert alpha.company_name == "Alpha"
    assert alpha.sector == "Technology"
    assert alpha.exchange == "NASDAQ"
