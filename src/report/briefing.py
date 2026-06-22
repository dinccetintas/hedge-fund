"""Render a `Briefing` to dated markdown (reports/YYYY-MM-DD.md).

The same `Briefing` object backs the web dashboard, so the markdown and the dashboard never
diverge. Every number traces back to the agent outputs that produced it.
"""

from __future__ import annotations

from pathlib import Path

from ..schemas import Briefing, Idea

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def _pct(x: float | None) -> str:
    return f"{x:.0%}" if isinstance(x, (int, float)) else "—"


def _num(x: float | None) -> str:
    return f"{x:,.2f}" if isinstance(x, (int, float)) else "—"


def _idea_section(i: Idea, rank: int) -> str:
    q, v, b, e, s = i.quality, i.valuation, i.bear_case, i.edge, i.sizing
    lines = [
        f"## {rank}. {i.ticker} — {i.company_name}",
        "",
        f"**Thesis.** {i.thesis_one_line}",
        "",
        f"**Why now.** {i.why_now}",
        "",
        f"- **Scout:** {i.scout.value}" + (f"  |  **Theme:** {i.theme}" if i.theme else ""),
        f"- **Conviction:** {_num(s.conviction) if s else '—'}/10"
        f"  |  **Rank score:** {_num(i.rank_score)}",
    ]
    if q:
        moat = ", ".join(f"{m.name} {m.score:g}/10 ({m.direction})" for m in q.moat[:5])
        lines.append(
            f"- **Quality:** {q.quality_score:g}/10  |  ROIC {_pct(q.roic)}  |  moat: {moat}"
        )
    if v:
        lines.append(
            f"- **Valuation:** buy-below **{_num(v.buy_below_price)}** "
            f"(now {_num(v.current_price)})"
            f"  |  5-yr IRR {_pct(v.expected_irr_5yr)}  |  MoS {_pct(v.margin_of_safety)}"
            f"  |  implied vs achievable growth {_pct(v.reverse_dcf_implied_growth)} / "
            f"{_pct(v.achievable_growth_estimate)}"
        )
    if b:
        lines.append(f"- **Bear case.** {b.summary}")
        if b.asymmetry_ratio is not None:
            lines.append(f"  - Asymmetry (up/down): **{_num(b.asymmetry_ratio)}×**"
                         f"  |  downside floor {_num(b.downside_floor_price)}")
        tripped = [f.name for f in b.red_flags if f.tripped]
        if tripped:
            lines.append(f"  - 🚩 Red flags: {', '.join(tripped)}")
        if b.invalidation_markers:
            lines.append("  - Invalidation markers: " + "; ".join(b.invalidation_markers[:5]))
    if e:
        verdict = "PASS" if e.passes else "FAIL"
        lines.append(f"- **Edge gate:** {verdict}"
                     + (f" — {e.time_arbitrage_rationale}" if e.time_arbitrage_rationale else ""))
    if s:
        lines.append(
            f"- **Sizing:** target "
            f"{_pct(s.target_weight_pct / 100 if s.target_weight_pct else None)}"
            f" (start {_pct(s.starter_weight_pct / 100 if s.starter_weight_pct else None)})"
            f"  |  entry {_num(s.entry_zone_low)}–{_num(s.entry_zone_high)}"
        )
        if s.sell_rules:
            lines.append("  - Sell rules: " + "; ".join(s.sell_rules[:3]))
    lines.append("")
    return "\n".join(lines)


def render_markdown(briefing: Briefing) -> str:
    head = [
        f"# Morning Briefing — {briefing.run_date.isoformat()}",
        "",
        f"*{len(briefing.ideas)} ranked ideas*"
        + (f"  ·  run `{briefing.run_id}`" if briefing.run_id else ""),
        "",
    ]
    if briefing.market_regime_note:
        head += [f"**Market regime.** {briefing.market_regime_note}", ""]
    if briefing.active_themes:
        head += ["**Active themes:** " + ", ".join(briefing.active_themes), ""]
    if briefing.watchlist_alerts:
        head += ["**Watchlist alerts:**", *(f"- {a}" for a in briefing.watchlist_alerts), ""]
    head += ["---", ""]

    if not briefing.ideas:
        body = ["_No ideas cleared the funnel today._"]
    else:
        body = [_idea_section(i, n) for n, i in enumerate(briefing.ideas, 1)]

    foot = [
        "---",
        "",
        "*Decision-support only — not investment advice, and no trades are placed. "
        "Every figure traces to the logged agent outputs + dated evidence in `store/`.*",
    ]
    return "\n".join(head + body + foot) + "\n"


def write_briefing(briefing: Briefing, reports_dir: Path = REPORTS_DIR) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{briefing.run_date.isoformat()}.md"
    path.write_text(render_markdown(briefing), encoding="utf-8")
    return path
