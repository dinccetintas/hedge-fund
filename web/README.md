# web/ — the dashboard (Phase 4)

The investor-grade daily surface. Built in **Phase 4**; this directory is a placeholder until then.

See `../docs/METHODOLOGY.md` §5c for the full design. Summary of confirmed decisions:

- **Stack:** Next.js + shadcn/ui (vendored) + Tremor (analytics charts/KPIs) + TradingView
  lightweight-charts (candlesticks). Deployed on Vercel.
- **Design language:** dark "modern terminal" (Bloomberg-meets-Linear), balanced-modern density.
- **Data source:** statically generated from each daily run's output (the `Briefing` JSON +
  `src/store/`). The dashboard never re-runs analysis — it renders logged, audited run data, so
  the markdown briefing and the dashboard can never diverge.

## Screens
1. **Today** — morning briefing: regime/themes strip, portfolio P&L, ranked opportunity cards.
2. **Stock Deep-Dive `/stock/[ticker]`** — candlestick (with entry-zone/buy-below bands) + thesis
   + **the Analyst Desk** (every persona's verdict side-by-side, with reasoning + cited sources) +
   financials overlay + news/sentiment timeline + thesis history.
3. **Themes & Outlook** — Citrini-style theme tracker (1st/2nd-order beneficiaries).
4. **Watchlist** — tracked theses, entry levels, alerts.
5. **Portfolio & Track Record** — positions vs targets, P&L, hit-rate, calibration curve.
6. **Research Log** — every run as a full audit trail (briefing → stock → persona → evidence).

**Traceability is a first-class feature:** every score/claim links to its dated source.
