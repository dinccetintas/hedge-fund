"""Each scout against the fixture universe + fake providers."""

from __future__ import annotations

from datetime import date

from src.data.bigdata_client import Document
from src.schemas import ScoutType
from src.scouts.base import ScoutContext
from src.scouts.contrarian import ContrarianScout
from src.scouts.hidden_gem import HiddenGemScout
from src.scouts.quality_compounder import QualityCompounderScout
from src.scouts.special_situations import SpecialSituationsScout
from src.scouts.thematic import ThematicScout, _Beneficiary, _Extraction
from tests.conftest import FakeBigdata, FakeFMP


def _ctx(fmp, universe, as_of, bigdata=None):
    return ScoutContext(fmp=fmp, universe=universe, as_of=as_of, bigdata=bigdata, enrich_cap=50)


async def test_quality_compounder_keeps_high_roic_grower(universe, as_of):
    fmp = FakeFMP(
        key_metrics={
            "AAA": [{"roic": 0.25, "peRatio": 25.0}],   # qualifies
            "BBB": [{"roic": 0.05, "peRatio": 18.0}],   # ROIC too low
        },
        growth={
            "AAA": [{"revenueGrowth": 0.15}],
            "BBB": [{"revenueGrowth": 0.20}],
        },
    )
    out = await QualityCompounderScout().source(_ctx(fmp, universe, as_of))
    tickers = {c.ticker for c in out}
    assert "AAA" in tickers
    assert "BBB" not in tickers
    assert all(c.scout is ScoutType.QUALITY_COMPOUNDER for c in out)


async def test_hidden_gem_band(universe, as_of):
    fmp = FakeFMP(
        key_metrics={
            "CCC": [{"roic": 0.18, "peRatio": 12.0}],   # small-cap, in band → qualifies
            "DDD": [{"roic": 0.18, "peRatio": 30.0}],   # P/E too high
        },
    )
    out = await HiddenGemScout().source(_ctx(fmp, universe, as_of))
    tickers = {c.ticker for c in out}
    assert "CCC" in tickers
    assert "DDD" not in tickers


async def test_contrarian_drawdown_with_growth(universe, as_of):
    fmp = FakeFMP(
        profiles={"EEE": {"range": "50-100", "price": 60.0}},  # 40% below high
        growth={"EEE": [{"revenueGrowth": 0.10}]},             # still growing
    )
    out = await ContrarianScout().source(_ctx(fmp, universe, as_of))
    assert {c.ticker for c in out} >= {"EEE"}


async def test_special_situations_ipo_and_forced_selling(universe, as_of):
    fmp = FakeFMP(
        ipos=[{"symbol": "FFF", "date": "2026-03-15"}],
        profiles={"GGG": {"range": "100-200", "price": 40.0}},  # 80% drawdown
    )
    out = await SpecialSituationsScout().source(_ctx(fmp, universe, as_of))
    tickers = {c.ticker for c in out}
    assert "FFF" in tickers  # recent IPO
    assert "GGG" in tickers  # forced selling


async def test_thematic_maps_beneficiaries_to_universe(universe, as_of):
    docs = [Document(
        headline="Memory shortage looms", source_name="Bigdata.com",
        published=date(2026, 5, 20), url=None, excerpt="DRAM tightness…", entities=["AAA"],
    )]

    async def fake_llm(_docs, _tickers):
        return _Extraction(beneficiaries=[
            _Beneficiary(ticker="AAA", theme="AI memory demand", order="second",
                         reason="key DRAM supplier"),
            _Beneficiary(ticker="ZZZ", theme="AI memory demand", order="first",
                         reason="not in universe"),
        ])

    scout = ThematicScout(llm_step=fake_llm)
    out = await scout.source(_ctx(fmp=FakeFMP(), universe=universe, as_of=as_of,
                                  bigdata=FakeBigdata(docs)))
    tickers = {c.ticker for c in out}
    assert "AAA" in tickers          # resolved to the universe
    assert "ZZZ" not in tickers      # dropped (not investable)
    assert out[0].theme == "AI memory demand"


async def test_thematic_skips_without_bigdata(universe, as_of):
    # No bigdata provided and no key → graceful empty result, not a crash.
    out = await ThematicScout().source(_ctx(FakeFMP(), universe, as_of, bigdata=None))
    assert out == []
