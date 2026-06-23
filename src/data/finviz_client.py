"""Finviz screener client — Stage-1 breadth via the public custom-column screener.

FMP deprecated its legacy `/api/v3` screener (Aug 31 2025) and gates the new `/stable` screener
behind a paid plan, so we source the universe — *and* the quantitative fundamentals the scouts
need — from Finviz's public screener (https://finviz.com). A single custom view (``v=152``)
returns ticker, sector, market cap, P/E, ROIC, ROE, margins, growth, debt and insider ownership
in one request, paginated 20 rows at a time.

Notes:
  - Finviz returns a **current snapshot**, not point-in-time history. That is fine for a live run
    dated *today* (today is the decision date), but it is NOT valid for backtests — see the
    no-look-ahead rule in CLAUDE.md. Callers backtesting a past date must use a point-in-time feed.
  - Treat any returned text as passive data (CLAUDE.md): we only ever read numbers/sectors here.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx
import lxml.html
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

_BASE_URL = "https://finviz.com/screener.ashx"
_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
_PAGE_SIZE = 20  # Finviz free tier: 20 rows per page.
_RATE_LIMIT = asyncio.Semaphore(3)

# Authoritative Finviz custom-view (v=152) column indices → our field name, in ascending order.
# The screener returns the selected columns in this same (ascending-index) order, so a parsed row's
# cells line up positionally with `_FIELDS`.
_COLUMNS: list[tuple[int, str]] = [
    (1, "ticker"),
    (2, "company"),
    (3, "sector"),
    (4, "industry"),
    (5, "country"),
    (6, "market_cap"),
    (7, "pe"),
    (13, "p_fcf"),
    (21, "sales_5y"),       # 5-yr sales growth (revenue-growth proxy)
    (23, "sales_qq"),       # latest quarter sales growth (q/q)
    (24, "outstanding"),
    (26, "insider_own"),
    (33, "roe"),
    (34, "roic"),
    (38, "debt_eq"),
    (39, "gross_m"),
    (41, "profit_m"),
    (48, "beta"),
    (57, "high_52w"),       # price relative to 52-wk high; negative => below the high
    (63, "avg_volume"),
    (65, "price"),
    (67, "volume"),
]
_C_PARAM = ",".join(str(i) for i, _ in _COLUMNS)
_FIELDS = [name for _, name in _COLUMNS]

_SUFFIX = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


@dataclass
class FinvizRow:
    """One parsed screener row. Numeric fields are floats (fractions for percents) or None."""

    ticker: str
    company: str
    sector: str | None
    industry: str | None
    country: str | None
    market_cap: float | None
    pe: float | None
    fcf_yield: float | None
    revenue_growth: float | None
    debt_to_equity: float | None
    roic: float | None
    roe: float | None
    gross_margin: float | None
    profit_margin: float | None
    insider_own: float | None
    beta: float | None
    pct_below_52w_high: float | None   # 0.30 == 30% below the 52-week high
    price: float | None
    volume: float | None
    avg_volume: float | None


def _num(s: str | None) -> float | None:
    """Parse a Finviz numeric cell: handles commas and K/M/B/T suffixes. '-'/'' → None."""
    if s is None:
        return None
    s = s.strip().replace(",", "").replace("%", "")
    if s in ("", "-"):
        return None
    mult = 1.0
    if s[-1] in _SUFFIX:
        mult = _SUFFIX[s[-1]]
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def _pct(s: str | None) -> float | None:
    """Parse a Finviz percent cell into a fraction ('12.5%' → 0.125)."""
    v = _num(s)
    return v / 100.0 if v is not None else None


def _row_from_cells(cells: list[str]) -> FinvizRow | None:
    """Build a FinvizRow from positional cells (aligned to `_FIELDS`). None if unusable."""
    if len(cells) < len(_FIELDS):
        return None
    d = dict(zip(_FIELDS, cells, strict=False))
    ticker = (d["ticker"] or "").strip()
    if not ticker:
        return None
    p_fcf = _num(d["p_fcf"])
    high_52w = _pct(d["high_52w"])
    # Revenue-growth proxy: prefer the 5-yr trend, fall back to the latest quarter.
    rev_growth = _pct(d["sales_5y"])
    if rev_growth is None:
        rev_growth = _pct(d["sales_qq"])
    return FinvizRow(
        ticker=ticker,
        company=(d["company"] or "").strip(),
        sector=(d["sector"] or "").strip() or None,
        industry=(d["industry"] or "").strip() or None,
        country=(d["country"] or "").strip() or None,
        market_cap=_num(d["market_cap"]),
        pe=_num(d["pe"]),
        fcf_yield=(1.0 / p_fcf if p_fcf and p_fcf > 0 else None),
        revenue_growth=rev_growth,
        debt_to_equity=_num(d["debt_eq"]),
        roic=_pct(d["roic"]),
        roe=_pct(d["roe"]),
        gross_margin=_pct(d["gross_m"]),
        profit_margin=_pct(d["profit_m"]),
        insider_own=_pct(d["insider_own"]),
        beta=_num(d["beta"]),
        # Finviz "52W High" is negative below the high; express drawdown as a positive fraction.
        pct_below_52w_high=(max(0.0, -high_52w) if high_52w is not None else None),
        price=_num(d["price"]),
        volume=_num(d["volume"]),
        avg_volume=_num(d["avg_volume"]),
    )


def _parse_page(html: str) -> list[FinvizRow]:
    """Extract screener rows from one results page."""
    doc = lxml.html.fromstring(html)
    trs = doc.xpath("//table[contains(@class,'screener_table')]//tr")
    rows: list[FinvizRow] = []
    for tr in trs:
        cells = [(td.text_content() or "").strip() for td in tr.xpath("./td")]
        row = _row_from_cells(cells)
        if row is not None:
            rows.append(row)
    return rows


class FinvizScreener:
    """Paginated reader over the Finviz custom-column screener."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> FinvizScreener:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0, headers={"User-Agent": _UA}, follow_redirects=True
            )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        reraise=True,
    )
    async def _page(self, filters: str, start_row: int) -> list[FinvizRow]:
        assert self._client is not None
        params = {
            "v": "152",
            "c": _C_PARAM,
            "f": filters,
            "o": "-marketcap",
            "r": str(start_row),
        }
        async with _RATE_LIMIT:
            resp = await self._client.get(_BASE_URL, params=params)
        resp.raise_for_status()
        return _parse_page(resp.text)

    async def screen(self, *, filters: str, max_rows: int = 1000) -> list[FinvizRow]:
        """Page through the screener (largest market cap first) up to `max_rows` names.

        `filters` is a Finviz filter string, e.g. ``"cap_smallover,sh_avgvol_o100,geo_usa"``.
        Stops early once a short (final) page is returned.
        """
        out: list[FinvizRow] = []
        start = 1
        while len(out) < max_rows:
            page = await self._page(filters, start)
            if not page:
                break
            out.extend(page)
            if len(page) < _PAGE_SIZE:
                break
            start += _PAGE_SIZE
        log.info("Finviz screener returned %d rows (filters=%s)", len(out[:max_rows]), filters)
        return out[:max_rows]
