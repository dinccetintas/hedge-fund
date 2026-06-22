"""CLI entry point: `python -m src.orchestrator [--stage1]`.

`--stage1` runs only the sourcing stage (Phase 1): build the universe, run the scout swarm,
persist + print the candidate list. With no flag it attempts the full funnel (Stages 2–7 land in
Phase 2, so it stops after sourcing for now).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import date

from rich.console import Console
from rich.table import Table

from ..data.fmp_client import FMPError
from ..settings import settings
from .run import run_daily, source_stage1

console = Console()

FUNNEL = (
    "[1] SOURCE → [2] QUALITY → [3] VALUE → [4] RED TEAM → "
    "[5] EDGE GATE → [6] SIZE → [7] SYNTHESIZE"
)


def _render(candidates) -> None:
    table = Table(title=f"Stage-1 candidates ({len(candidates)})", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Scout", style="magenta")
    table.add_column("Why", overflow="fold")
    for i, c in enumerate(candidates, 1):
        table.add_row(str(i), c.ticker, c.scout.value, c.one_line_reason)
    console.print(table)


async def _stage1() -> None:
    run_id, candidates = await source_stage1()
    _render(candidates)
    console.print(f"\nPersisted run [green]{run_id}[/] → store/runs/{date.today().isoformat()}/")
    if not candidates:
        console.print(
            "[yellow]No candidates.[/] Check that FMP_API_KEY is set and the screener returned "
            "rows (free-tier limits may apply)."
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="bear-run")
    parser.add_argument("--stage1", action="store_true", help="run only Stage-1 sourcing")
    args = parser.parse_args()

    logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s: %(message)s")
    console.rule("[bold]Project Bear Stearns — daily research run")
    console.print(f"Run date: [cyan]{date.today().isoformat()}[/]")
    console.print(f"Funnel:   {FUNNEL}\n")

    try:
        if args.stage1:
            asyncio.run(_stage1())
        else:
            asyncio.run(run_daily())
    except FMPError as e:
        console.print(f"[red]Data error:[/] {e}")
    except NotImplementedError as e:
        console.print(f"[yellow]Funnel stops here:[/] {e}")


if __name__ == "__main__":
    main()
