"""Proven-model-transplant scout (Oguz) — the "Amazon-of-X" pattern.

A de-risked business model entering an underpenetrated market/geography: the model risk is already
retired elsewhere, so the bet is execution + TAM. Detect these from Bigdata.com narratives and map
to liquid-universe tickers. Same graceful-degradation + injectable-LLM design as the thematic scout.
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

PROBES = [
    "company replicating a proven business model in a new underpenetrated market or geography",
    "the leading challenger bringing an established Western business model to an emerging market",
]


class _Transplant(BaseModel):
    ticker: str
    company_name: str = ""
    proven_model: str = Field(description="The de-risked model being transplanted.")
    new_market: str = Field(description="The underpenetrated market it is entering.")
    reason: str


class _Extraction(BaseModel):
    transplants: list[_Transplant] = Field(default_factory=list)


LLMStep = Callable[[list[Document], list[str]], Awaitable[_Extraction]]


class TransplantScout(Scout):
    scout_type = ScoutType.TRANSPLANT

    def __init__(self, llm_step: LLMStep | None = None):
        self._llm_step = llm_step or self._default_llm_step

    async def source(self, ctx: ScoutContext, *, limit: int = 25) -> list[Candidate]:
        bigdata = ctx.bigdata or BigdataClient()
        if not bigdata.available:
            log.warning("Transplant scout skipped — Bigdata.com unavailable (no BIGDATA_API_KEY).")
            return []

        docs: list[Document] = []
        for probe in PROBES:
            try:
                docs.extend(await bigdata.search(probe, until=ctx.as_of, max_chunks=15))
            except (BigdataUnavailable, NotImplementedError) as e:
                log.warning("Transplant scout skipped — %s", e)
                return []
        if not docs:
            return []

        extraction = await self._llm_step(docs, list(ctx.by_ticker.keys()))

        out: list[Candidate] = []
        seen: set[str] = set()
        for t in extraction.transplants:
            stock = ctx.by_ticker.get(t.ticker.upper())
            if stock is None or stock.ticker in seen:
                continue
            seen.add(stock.ticker)
            theme = f"{t.proven_model} → {t.new_market}"
            ev = Evidence(
                claim=f"{t.ticker} transplants {t.proven_model} into {t.new_market}. {t.reason}",
                source_type=SourceType.NEWS,
                source_name="Bigdata.com",
                source_date=ctx.as_of,
                url="https://bigdata.com",
            )
            out.append(
                self._candidate(
                    stock,
                    f"Proven model in a new market — {theme}: {t.reason}",
                    theme=theme,
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
            "You are an equity scout hunting the 'proven model in a new market' pattern (Oguz "
            "Erkan): a de-risked business model entering an underpenetrated geography or vertical. "
            "Only return US-listed tickers."
        )
        user = (
            f"Recent documents:\n{corpus}\n\nReturn transplant candidates as JSON. Prefer tickers "
            f"from this universe when applicable: {', '.join(universe_tickers[:800])}"
        )
        return await structured(
            model=settings.model_screen,
            system=system,
            user=user,
            schema=_Extraction,
            max_tokens=2000,
        )
