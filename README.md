# Project "Bear Stearns" — Personal AI Opportunity Finder

> Decision-support, not auto-trading. An AI research system that hunts the broad US market every
> morning and presents a ranked briefing — thesis, bear case, entry levels, risk-defined sizing —
> so a busy human just reviews and decides.

## Why

The goal is to **clone and scale one investor's proven edge**: asymmetric, pre-consensus bets
(the kind that found MU ~2 years before the memory-shortage thesis went mainstream). One person
working a 9–5 cannot scan thousands of stocks; this system does the scanning and reasoning, then
surfaces a short, high-conviction shortlist each day.

**North-star:** grow a $10,000 book ~5x over a multi-year horizon by concentrating capital in a
small number of asymmetric, well-understood ideas with defined downside. We optimize for
**expected value under uncertainty** (probability × payoff).

## How it works — the 7-stage funnel

Each daily run turns the whole US market into a short ranked shortlist:

```
[1] SOURCE → [2] QUALITY → [3] VALUE → [4] RED TEAM → [5] EDGE GATE → [6] SIZE → [7] SYNTHESIZE
```

Each stage is an **agent** encoding the technique of documented, S&P-beating equity researchers
(see [`methodology/`](methodology/)). The orchestrator (Claude Code) runs the funnel, spawns the
persona agents, logs everything, and writes the morning briefing.

| Stage | Agent | Output |
|---|---|---|
| 1 | **Scout swarm** (6 sourcing patterns) | daily candidate list |
| 2 | **Moat / Quality Analyst** | Quality Score /10 |
| 3 | **Valuation Analyst** | 5-yr IRR/EV + buy-below price |
| 4 | **Red Team / Forensic** | bear case + invalidation markers |
| 5 | **Edge Gate (Behavioral)** | pass/fail "is it really mispriced?" |
| 6 | **Risk & Portfolio Manager** | position size + entry plan |
| 7 | **Orchestrator** | ranked morning briefing + watchlist update |

The full methodology and house view live in
[`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) (the approved ideation deliverable).

## Architecture

- **Backend / agents:** Python. Each agent = a Claude call with relevant `methodology/` context,
  a structured-output schema (machine-readable scores/IRR/sizing), and cited, dated evidence.
- **Data:** FMP (Financial Modeling Prep) primary feed — fundamentals, prices, earnings, screener;
  **Bigdata.com** (https://bigdata.com) for news / sentiment / events / filings / transcripts.
- **Storage:** git-tracked SQLite + JSON — every run, thesis, and trade is versioned and auditable.
- **Delivery:** dated markdown briefing → Next.js dashboard on Vercel.
- **Scheduling:** GitHub Action cron (daily morning run).
- **LLM:** Claude — Opus for deep synthesis, Sonnet/Haiku for bulk screening (cost-aware routing).

```
hedge-fund/
├── docs/METHODOLOGY.md   # the approved plan: house view, funnel, agents, roadmap
├── methodology/          # knowledge base — one .md per master, loaded into agent prompts
├── src/                  # data layer, scouts, agents, orchestrator, store, report
├── reports/              # YYYY-MM-DD.md briefings (git-tracked history)
├── web/                  # Next.js dashboard (Vercel) — Phase 4
└── .github/workflows/    # scheduled daily run — Phase 3
```

## Status

Built in phases (see `docs/METHODOLOGY.md` §6):

- [x] **Phase 0** — Ideation & scaffolding
- [x] **Phase 1** — Data layer + Scout screens (FMP client, universe builder, 6 scouts, store)
- [ ] **Phase 2** — The funnel (agents 2–7) → dated markdown briefing
- [ ] **Phase 3** — Watchlist monitor + portfolio tracker + scheduling
- [ ] **Phase 4** — Web dashboard
- [ ] **Phase 5** — Track record & tuning

## Setup

```bash
# 1. Python env (uv recommended)
uv sync                      # or: pip install -e ".[dev]"

# 2. Secrets
cp .env.example .env         # then fill in FMP_API_KEY, ANTHROPIC_API_KEY, ...

# 3. Run Stage-1 sourcing (Phase 1): universe → scout swarm → candidate list
python -m src.orchestrator --stage1     # persists store/runs/<date>/candidates.json

# (Phase 2+) the full funnel → reports/YYYY-MM-DD.md
python -m src.orchestrator
```

## Disclaimer

This is a personal research and decision-support tool. It is **not** investment advice and does
**not** place trades. All researcher performance figures referenced in `methodology/` are
self-reported/unverified unless noted. Do your own due diligence.
