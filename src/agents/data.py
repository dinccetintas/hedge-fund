"""The per-candidate data packet the analysis agents reason over.

`gather_company_data` pulls a candidate's point-in-time fundamentals/prices from FMP; `to_prompt`
renders them into a compact, dated text block for the LLM. Built once per candidate and shared
across Stages 2–6 so we pay for the data pulls only once. Tests construct `CompanyData` directly,
so the agents need no live FMP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from ..data.fmp_client import FMPClient
from ..scouts.enrich import drawdown_from_high


@dataclass
class CompanyData:
    ticker: str
    as_of: date
    profile: dict[str, Any] = field(default_factory=dict)
    key_metrics: list[dict[str, Any]] = field(default_factory=list)   # newest first
    ratios: list[dict[str, Any]] = field(default_factory=list)
    income: list[dict[str, Any]] = field(default_factory=list)
    balance: list[dict[str, Any]] = field(default_factory=list)
    cash_flow: list[dict[str, Any]] = field(default_factory=list)
    growth: list[dict[str, Any]] = field(default_factory=list)
    prices: list[dict[str, Any]] = field(default_factory=list)
    news: list[str] = field(default_factory=list)  # optional Bigdata.com snippets

    @property
    def current_price(self) -> float | None:
        if self.prices:
            return self.prices[0].get("close")
        return self.profile.get("price")

    def to_prompt(self) -> str:
        """A compact, dated snapshot for the model. Keeps a few years of history, newest first."""
        p = self.profile
        lines = [
            f"Ticker: {self.ticker}  (data as of {self.as_of.isoformat()})",
            f"Company: {p.get('companyName', '?')}  |  Sector: {p.get('sector', '?')}  |  "
            f"Industry: {p.get('industry', '?')}",
            f"Price: {self.current_price}  |  Market cap: {p.get('mktCap') or p.get('marketCap')}  "
            f"|  Beta: {p.get('beta')}  |  52-wk range: {p.get('range')}",
        ]
        dd = drawdown_from_high(p)
        if dd is not None:
            lines.append(f"Drawdown from 52-wk high: {dd:.0%}")
        if p.get("description"):
            lines.append(f"Business: {str(p['description'])[:600]}")

        lines.append("\nKey metrics (newest first):")
        for i, km in enumerate(self.key_metrics[:5]):
            r = self.ratios[i] if i < len(self.ratios) else {}
            roic = km.get("returnOnInvestedCapital", km.get("roic"))
            pe = r.get("priceToEarningsRatio", km.get("peRatio"))
            de = r.get("debtToEquityRatio", km.get("debtToEquity"))
            net_margin = r.get("netProfitMargin")
            lines.append(
                f"  {km.get('date', '?')}: ROIC={_pct(roic)}, P/E={_round(pe)}, "
                f"net margin={_pct(net_margin)}, FCF yield={_pct(km.get('freeCashFlowYield'))}, "
                f"D/E={_round(de)}"
            )
        lines.append("Growth (newest first):")
        for g in self.growth[:5]:
            lines.append(
                f"  {g.get('date', '?')}: revenueGrowth={g.get('revenueGrowth')}, "
                f"epsGrowth={g.get('epsgrowth') or g.get('epsGrowth')}"
            )
        lines.append("Income (newest first):")
        for inc in self.income[:4]:
            lines.append(
                f"  {inc.get('date', '?')}: revenue={inc.get('revenue')}, "
                f"grossMargin={_ratio(inc.get('grossProfit'), inc.get('revenue'))}, "
                f"netIncome={inc.get('netIncome')}"
            )
        if self.news:
            lines.append("\nRecent context (Bigdata.com):")
            lines.extend(f"  - {n}" for n in self.news[:8])
        return "\n".join(lines)


def _ratio(num: Any, den: Any) -> str:
    try:
        return f"{num / den:.2f}"
    except (TypeError, ZeroDivisionError):
        return "?"


def _pct(v: Any) -> str:
    """Render a fraction as a percent, or '?' if missing/non-numeric."""
    try:
        return f"{float(v):.1%}"
    except (TypeError, ValueError):
        return "?"


def _round(v: Any) -> str:
    try:
        return f"{float(v):.1f}"
    except (TypeError, ValueError):
        return "?"


async def gather_company_data(
    fmp: FMPClient, ticker: str, as_of: date, *, news: list[str] | None = None
) -> CompanyData:
    """Pull the point-in-time data packet for one candidate (best-effort per endpoint)."""
    import asyncio

    async def safe(coro):
        try:
            return await coro
        except Exception:  # noqa: BLE001 — premium-gated/missing endpoints degrade to empty
            return None

    profile, key_metrics, ratios, income, balance, cash_flow, growth, prices = await asyncio.gather(
        safe(fmp.profile(ticker, as_of=as_of)),
        safe(fmp.key_metrics(ticker, period="annual", limit=5, as_of=as_of)),
        safe(fmp.ratios(ticker, period="annual", limit=5, as_of=as_of)),
        safe(fmp.income_statement(ticker, period="annual", limit=5, as_of=as_of)),
        safe(fmp.balance_sheet(ticker, period="annual", limit=5, as_of=as_of)),
        safe(fmp.cash_flow(ticker, period="annual", limit=5, as_of=as_of)),
        safe(fmp.financial_growth(ticker, period="annual", limit=5, as_of=as_of)),
        safe(fmp.prices(ticker, as_of=as_of, lookback_days=400)),
    )
    return CompanyData(
        ticker=ticker,
        as_of=as_of,
        profile=profile or {},
        key_metrics=key_metrics or [],
        ratios=ratios or [],
        income=income or [],
        balance=balance or [],
        cash_flow=cash_flow or [],
        growth=growth or [],
        prices=prices or [],
        news=news or [],
    )
