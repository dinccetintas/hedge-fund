"""Aggregation dedupe-merge behavior."""

from __future__ import annotations

from datetime import date

from src.schemas import Candidate, Evidence, ScoutType, SourceType
from src.scouts.aggregate import _merge


def _cand(ticker, scout, reason, claim):
    return Candidate(
        ticker=ticker, company_name=f"{ticker} Inc", scout=scout, one_line_reason=reason,
        evidence=[Evidence(claim=claim, source_type=SourceType.FUNDAMENTAL,
                           source_name="FMP", source_date=date(2026, 6, 1))],
    )


def test_merge_combines_multi_scout_hits():
    a = _cand("AAA", ScoutType.QUALITY_COMPOUNDER, "high ROIC", "roic 25%")
    b = _cand("AAA", ScoutType.CONTRARIAN, "down 40%", "drawdown")
    c = _cand("BBB", ScoutType.HIDDEN_GEM, "cheap small-cap", "pe 11")

    merged = _merge([a, b, c])

    by_ticker = {m.ticker: m for m in merged}
    assert set(by_ticker) == {"AAA", "BBB"}
    # AAA found by two scouts: both reasons + both evidence retained.
    assert "high ROIC" in by_ticker["AAA"].one_line_reason
    assert "down 40%" in by_ticker["AAA"].one_line_reason
    assert len(by_ticker["AAA"].evidence) == 2
    # Multi-scout name sorts ahead of single-scout name.
    assert merged[0].ticker == "AAA"
