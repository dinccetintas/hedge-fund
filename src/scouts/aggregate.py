"""Run all six scouts concurrently and merge their candidates.

A ticker found by multiple scouts is a stronger signal, so we **merge** rather than drop: the
surviving `Candidate` keeps every scout's attribution (reasons + evidence). The PM at Stage 7
still ranks regardless of which scout found a name.
"""

from __future__ import annotations

import asyncio
import logging

from ..schemas import Candidate, ScoutType
from .base import Scout, ScoutContext
from .contrarian import ContrarianScout
from .hidden_gem import HiddenGemScout
from .quality_compounder import QualityCompounderScout
from .special_situations import SpecialSituationsScout
from .thematic import ThematicScout
from .transplant import TransplantScout

log = logging.getLogger(__name__)


def all_scouts() -> list[Scout]:
    """The default scout swarm (balanced composite — see src.config.SCOUT_WEIGHTS)."""
    return [
        ThematicScout(),
        TransplantScout(),
        QualityCompounderScout(),
        HiddenGemScout(),
        SpecialSituationsScout(),
        ContrarianScout(),
    ]


async def source_candidates(
    ctx: ScoutContext, *, scouts: list[Scout] | None = None, per_scout_limit: int = 25
) -> list[Candidate]:
    """Source from every scout in parallel, then dedupe-merge by ticker."""
    scouts = scouts or all_scouts()

    async def run(scout: Scout) -> list[Candidate]:
        try:
            return await scout.source(ctx, limit=per_scout_limit)
        except Exception:  # noqa: BLE001 — one scout failing must not sink the run
            log.exception("Scout %s failed", scout.scout_type)
            return []

    results = await asyncio.gather(*(run(s) for s in scouts))
    return _merge([c for batch in results for c in batch])


def _merge(candidates: list[Candidate]) -> list[Candidate]:
    """Combine duplicate tickers, preserving all scout attributions and evidence."""
    merged: dict[str, Candidate] = {}
    extra_scouts: dict[str, set[ScoutType]] = {}
    for c in candidates:
        if c.ticker not in merged:
            merged[c.ticker] = c.model_copy(deep=True)
            extra_scouts[c.ticker] = {c.scout}
            continue
        base = merged[c.ticker]
        if c.scout not in extra_scouts[c.ticker]:
            extra_scouts[c.ticker].add(c.scout)
            base.one_line_reason += f"  |  [{c.scout.value}] {c.one_line_reason}"
        base.evidence.extend(c.evidence)
        if base.theme is None and c.theme is not None:
            base.theme = c.theme

    # Names found by more scouts sort first (stronger multi-signal).
    return sorted(merged.values(), key=lambda c: len(extra_scouts[c.ticker]), reverse=True)
