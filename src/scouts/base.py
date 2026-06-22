"""Common interface + shared context for all Stage-1 scouts."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from ..data.bigdata_client import BigdataClient
from ..data.fmp_client import FMPClient
from ..schemas import Candidate, Evidence, ScoutType, SourceType
from ..universe.build import UniverseStock

log = logging.getLogger(__name__)


@dataclass
class ScoutContext:
    """Everything a scout needs, built once per run and shared across all scouts."""

    fmp: FMPClient
    universe: list[UniverseStock]
    as_of: date
    bigdata: BigdataClient | None = None
    # Cap on per-scout fundamental enrichment calls (free-tier friendly; raise on Starter+).
    enrich_cap: int = 50
    by_ticker: dict[str, UniverseStock] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.by_ticker:
            self.by_ticker = {s.ticker: s for s in self.universe}


class Scout(ABC):
    """A single idea-sourcing pattern.

    Implementations filter the in-memory `ctx.universe` on always-available screener fields first
    (cheap, no extra calls), then best-effort enrich a bounded shortlist with fundamentals. They
    must only use data dated <= `ctx.as_of` (no look-ahead) and must degrade gracefully when an
    endpoint is premium-gated or Bigdata.com is unavailable.
    """

    scout_type: ScoutType

    @abstractmethod
    async def source(self, ctx: ScoutContext, *, limit: int = 25) -> list[Candidate]:
        """Return up to `limit` candidates this scout flags as of `ctx.as_of`."""
        ...

    # -- helpers shared by the quantitative scouts ------------------------------------------- #
    def _candidate(
        self, stock: UniverseStock, reason: str, *, theme: str | None = None,
        evidence: list[Evidence] | None = None,
    ) -> Candidate:
        return Candidate(
            ticker=stock.ticker,
            company_name=stock.company_name,
            scout=self.scout_type,
            one_line_reason=reason,
            theme=theme,
            evidence=evidence or [],
        )

    @staticmethod
    def _fundamental_evidence(claim: str, as_of: date, ticker: str) -> Evidence:
        return Evidence(
            claim=claim,
            source_type=SourceType.FUNDAMENTAL,
            source_name=f"FMP fundamentals ({ticker})",
            source_date=as_of,
        )
