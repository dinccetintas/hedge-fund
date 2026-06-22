"""Thematic / second-order scout (Citrini / Oguz) — **the MU engine**.

Detect accelerating secular themes from Bigdata.com, then map first- AND second-order
beneficiaries (the suppliers/enablers, not just the obvious name) and resolve them to tickers in
our liquid universe. This is the pattern that found MU as a memory-shortage beneficiary.

Degrades gracefully: with no Bigdata.com access it logs a warning and returns []. The LLM mapping
step is injectable so it can be unit-tested with fixtures.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from pydantic import BaseModel, Field

from ..data.bigdata_client import BigdataClient, BigdataUnavailable, Document
from ..llm import structured
from ..schemas import Candidate, Evidence, ScoutType, SourceType
from ..settings import settings
from .base import Scout, ScoutContext

log = logging.getLogger(__name__)

# Broad probes for "what is accelerating right now." One focus per Bigdata.com query.
THEME_PROBES = [
    "emerging secular technology trends accelerating in adoption and spending",
    "supply shortages and capacity constraints creating pricing power for suppliers",
    "new regulation or policy creating durable demand for specific industries",
]


class _Beneficiary(BaseModel):
    ticker: str
    company_name: str = ""
    theme: str
    order: str = Field(description="first | second")
    reason: str


class _Extraction(BaseModel):
    beneficiaries: list[_Beneficiary] = Field(default_factory=list)


# Injectable LLM step: (documents, universe_tickers) -> extraction. Defaults to a Haiku call.
LLMStep = Callable[[list[Document], list[str]], Awaitable[_Extraction]]


class ThematicScout(Scout):
    scout_type = ScoutType.THEMATIC

    def __init__(self, llm_step: LLMStep | None = None):
        self._llm_step = llm_step or self._default_llm_step

    async def source(self, ctx: ScoutContext, *, limit: int = 25) -> list[Candidate]:
        bigdata = ctx.bigdata or BigdataClient()
        if not bigdata.available:
            log.warning("Thematic scout skipped — Bigdata.com unavailable (no BIGDATA_API_KEY).")
            return []

        docs: list[Document] = []
        for probe in THEME_PROBES:
            try:
                docs.extend(await bigdata.search(probe, until=ctx.as_of, max_chunks=15))
            except (BigdataUnavailable, NotImplementedError) as e:
                log.warning("Thematic scout skipped — %s", e)
                return []
        if not docs:
            return []

        universe_tickers = list(ctx.by_ticker.keys())
        extraction = await self._llm_step(docs, universe_tickers)

        out: list[Candidate] = []
        seen: set[str] = set()
        for b in extraction.beneficiaries:
            stock = ctx.by_ticker.get(b.ticker.upper())
            if stock is None or stock.ticker in seen:
                continue
            seen.add(stock.ticker)
            ev = Evidence(
                claim=f"{b.ticker} is a {b.order}-order beneficiary of: {b.theme}. {b.reason}",
                source_type=SourceType.NEWS,
                source_name="Bigdata.com",
                source_date=ctx.as_of,
                url="https://bigdata.com",
            )
            out.append(
                self._candidate(
                    stock,
                    f"{b.order.capitalize()}-order beneficiary of {b.theme}: {b.reason}",
                    theme=b.theme,
                    evidence=[ev],
                )
            )
            if len(out) >= limit:
                break
        return out

    async def _default_llm_step(
        self, docs: list[Document], universe_tickers: list[str]
    ) -> _Extraction:
        corpus = "\n".join(
            f"- [{d.published}] {d.source_name}: {d.headline} — {d.excerpt}" for d in docs[:40]
        )
        system = (
            "You are a thematic equity scout in the style of Citrini Research. From recent "
            "documents, identify accelerating secular themes and the PUBLIC companies that "
            "benefit — emphasizing SECOND-ORDER beneficiaries (suppliers, enablers, picks-and-"
            "shovels), not just the obvious first-order name. Only return US-listed tickers."
        )
        user = (
            f"Recent documents:\n{corpus}\n\n"
            "Return beneficiaries as JSON. Prefer tickers from this investable universe when "
            f"applicable: {', '.join(universe_tickers[:800])}"
        )
        return await structured(
            model=settings.model_screen,
            system=system,
            user=user,
            schema=_Extraction,
            max_tokens=2000,
        )
