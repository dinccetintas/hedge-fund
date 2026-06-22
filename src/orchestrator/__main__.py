"""CLI entry point: `python -m src.orchestrator` (or `bear-run`).

In Phase 0 this prints the funnel overview and exits; once Phases 1–3 land it triggers a real
daily run and writes reports/YYYY-MM-DD.md.
"""

from __future__ import annotations

import asyncio
from datetime import date

from rich.console import Console

from .run import run_daily

console = Console()

FUNNEL = (
    "[1] SOURCE → [2] QUALITY → [3] VALUE → [4] RED TEAM → "
    "[5] EDGE GATE → [6] SIZE → [7] SYNTHESIZE"
)


def main() -> None:
    console.rule("[bold]Project Bear Stearns — daily research run")
    console.print(f"Run date: [cyan]{date.today().isoformat()}[/]")
    console.print(f"Funnel:   {FUNNEL}\n")
    try:
        asyncio.run(run_daily())
    except NotImplementedError as e:
        console.print(f"[yellow]Not yet wired:[/] {e}")
        console.print("Scaffold is in place. Implement Phase 1 (data + scouts) next.")


if __name__ == "__main__":
    main()
