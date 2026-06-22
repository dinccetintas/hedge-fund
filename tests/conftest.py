"""Shared test fixtures: a fake FMP, a fake Bigdata.com, and a small universe.

All fixture-based — no network. The fakes duck-type only the methods the scouts actually call.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.data.bigdata_client import Document
from src.universe.build import UniverseStock


class FakeFMP:
    """Duck-typed stand-in for FMPClient covering the methods scouts/enrich call."""

    def __init__(
        self,
        *,
        key_metrics: dict | None = None,
        growth: dict | None = None,
        profiles: dict | None = None,
        ipos: list | None = None,
        screener_rows: list | None = None,
    ):
        self._km = key_metrics or {}
        self._g = growth or {}
        self._p = profiles or {}
        self._ipos = ipos or []
        self._screener_rows = screener_rows or []

    async def screener(self, *, as_of=None, **filters):
        return self._screener_rows

    async def key_metrics(self, ticker, *, period="annual", limit=5, as_of=None):
        return self._km.get(ticker, [])

    async def financial_growth(self, ticker, *, period="annual", limit=5, as_of=None):
        return self._g.get(ticker, [])

    async def profile(self, ticker, *, as_of=None):
        return self._p.get(ticker, {})

    async def ipo_calendar(self, *, from_date, to_date):
        return self._ipos


class FakeBigdata:
    """Available Bigdata.com stand-in returning canned documents."""

    available = True

    def __init__(self, docs: list[Document]):
        self._docs = docs

    async def search(self, text, *, until, max_chunks=20):
        return self._docs


@pytest.fixture
def as_of() -> date:
    return date(2026, 6, 1)


@pytest.fixture
def universe() -> list[UniverseStock]:
    def stock(ticker, name, mcap, sector="Technology"):
        return UniverseStock(
            ticker=ticker, company_name=name, market_cap=mcap, sector=sector,
            industry="X", price=100.0, volume=1_000_000, exchange="NASDAQ",
        )

    return [
        stock("AAA", "Alpha Corp", 5_000_000_000),
        stock("BBB", "Beta Inc", 4_000_000_000),
        stock("CCC", "Gamma Ltd", 500_000_000),
        stock("DDD", "Delta Co", 600_000_000),
        stock("EEE", "Epsilon Inc", 1_000_000_000),
        stock("FFF", "Zeta Corp", 800_000_000),
        stock("GGG", "Eta Ltd", 1_200_000_000),
    ]
