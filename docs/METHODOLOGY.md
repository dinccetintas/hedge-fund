# Project "Bear Stearns" — Personal AI Opportunity Finder

## Context

**Why we're building this.** The user works a 9–5 and cannot manually scan thousands of
stocks, yet has a proven instinct for asymmetric, pre-consensus bets (self-found MU ~2 years
ago on a memory-shortage thesis → ~800% gain — a textbook *thematic / second-order beneficiary*
call). The goal is to **clone and scale that edge**: an AI research system that hunts the broad
US market for high-probability, undervalued, or pre-trend opportunities and, every morning,
presents a ranked briefing with a thesis, a bear case, entry levels, and risk-defined sizing —
so the user just reviews and decides. **Decision-support, not auto-trading.**

**North-star goal:** grow a $10,000 portfolio ~5x ($50k) over a multi-year horizon by
concentrating capital in a small number of asymmetric, well-understood ideas with defined
downside. We optimize for **expected value under uncertainty** (probability × payoff) — a few
MU-style winners drive the 5x.

**Confirmed product decisions (from user):**
- **Delivery:** Web dashboard (Next.js → Vercel), backed by a dated markdown report per run.
- **Universe:** Broad US stocks incl. small/mid-cap (where pre-trend, undervalued gems live).
- **Cadence:** Scheduled daily research run + watchlist monitor (not intraday/continuous).
- **Data budget:** ~$100–200/mo for paid APIs.

**Methodology research done (this is what makes the system good).** Rather than invent a
generic "value investing" process, we reverse-engineered the methodology of **14 documented,
S&P-beating equity researchers** plus macro/thematic and forensic short layers. The system's
"house view" below is a synthesis of their *convergent* principles, with each writer's
*distinctive* technique bolted on where it adds rigor. The six idea-sourcing scouts are weighted
as a **balanced composite** (equal weight, re-tunable from the track record in Phase 5), so the
user's thematic/second-order edge is one strong scout among several rather than the sole lens.
Full source library in §8.

> This plan file is the **ideation deliverable** (personas, goal, method, architecture). The
> heart is §3 (the methodology). Approving it kicks off Phase 1.

---

## 1. The Goal (measurable)

| Dimension | Target |
|---|---|
| Capital | $10,000 starting |
| Objective | ~5x → ~$50,000 over a multi-year horizon |
| Style | Concentrated, high-conviction position trades (months–years); not day-trading |
| Edge | Find asymmetric / pre-consensus ideas *before* they trend; define downside first |
| Risk | Per-idea downside capped; conviction-weighted sizing; concentration limits |
| Accountability | Log every recommendation; track hit-rate, avg R:R, realized vs predicted |

---

## 2. The House View — what 14 proven investors agree on (convergent core)

Beneath very different styles, the writers we studied converge on **9 principles**. These are
the system's non-negotiable beliefs — every recommendation is judged against them:

1. **Quality + a durable, *growing* moat is the substrate.** High & *sustainable* ROIC; market
   leadership. The margin of safety lives largely in the durability of the moat.
   *(Slegers, Speedwell, MBI, Leandro, Oguz)*
2. **Reinvestment runway × returns on *incremental* capital = the compounding engine.** This is
   the multibagger math; ~80% of long-run returns come from earnings growth + reinvestment, not
   multiple expansion. *(Giuliano's "reinvestment moat", Speedwell, MBI, Leandro)*
3. **Reverse DCF / "what do I need to believe?"** Don't forecast a point target — back out what
   the price *implies*, then test if the business can realistically clear that bar. Anchor the
   IRR hurdle to bond yields (~6–7% floor; equity must beat debt). *(MBI, Speedwell, Slegers,
   Leandro, Wolf, Oguz)*
4. **Downside first. "Heads we win, tails we don't lose much."** Define what can go wrong and
   what's already priced in *before* sizing the upside. *(Oguz, Walker, all)*
5. **Edge = depth + behavior, not information speed.** Informational edge is dead. Real edge =
   *analytical* × *behavioral* (patience / contrarianism / willingness to wait years the crowd
   won't). This time-arbitrage *is* the mispricing. *(Oguz, MBI, Morris)*
6. **Concentration + conviction sizing, never equal-weight.** ~8–15 names; biggest positions
   carry real weight. *(Morris top-5 >60%, Waller 7–8 names, MBI 10–20)*
7. **Start small; add only on validation.** Don't treat your assumptions as base case; double
   down only on theses that prove out *while the price still lags*. *(Oguz, Morris)*
8. **Long horizons; sell only on broken thesis (or consummated catalyst).** "Let winners run";
   beware thesis drift. Low turnover. *(Morris, Leandro, all)*
9. **Management & capital allocation are first-class variables.** Owner-operators / skin in the
   game (≥~10% ownership), high-ROIC reinvestment, value-unlocking. *(Slegers, Giuliano, Walker)*

---

## 3. The Method — the 7-stage research funnel (operationalized)

Each daily run executes this funnel, turning the whole US market into a short ranked shortlist.
Each stage names the **agent** that runs it and the **masters** whose technique it encodes.

```
[1] SOURCE → [2] QUALITY → [3] VALUE → [4] RED TEAM → [5] EDGE GATE → [6] SIZE → [7] SYNTHESIZE
```

**Stage 1 — Idea Sourcing** *(Scout agents, run in parallel)*
Six sourcing patterns, each a "scout," **weighted equally (balanced composite)** — the PM at
Stage 7 surfaces the best idea regardless of which scout found it. (Weights are a config knob we
can re-tune in Phase 5 from the track record.)
- **Thematic / second-order scout** *(Citrini, Oguz)* — detect accelerating secular trends from
  news/filings/reports (Bigdata.com), then map **first- AND second-order beneficiaries** (the
  suppliers/enablers, not just the obvious name). **This is the MU engine.**
- **Proven-model-transplant scout** *(Oguz)* — de-risked business model entering an
  underpenetrated market (the "Amazon-of-X" pattern).
- **Quality-compounder screen** *(Slegers, Giuliano, Rijnberk)* — high ROIC + reinvestment
  runway + organic growth ≥~7% at a reasonable price.
- **Hidden-gem small-cap screen** *(Waller)* — niche leaders, ~15–20% ROIC trading ~10–13×
  earnings, low analyst coverage.
- **Special-situations scout** *(Walker)* — spinoffs, forced selling as a *buy* signal, busted
  IPOs/SPACs, catalysts; "buy the better business in the spin."
- **Contrarian / divergence scout** *(Oguz, Leandro, App Economy)* — quality names sold off or
  ignored amid euphoria elsewhere; price diverging from north-star fundamentals.

**Stage 2 — Business Quality Analysis** *(Moat/Quality agent)* → a **Quality Score /10** (Slegers-style)
- Moat via **5-step competitive-advantage analysis** *(Oguz)* — network effects, switching
  costs, cost advantage, intangibles/brand, scale — scored on durability *and direction*.
- Returns on capital (ROIC high & sustainable; **returns on incremental capital**).
- Reinvestment runway (can it redeploy cash at high ROIC for a decade?).
- Growth quality — prefer **moderate-durable over hype-hypergrowth** (hypergrowth attracts
  capital that erodes margins) *(MBI)*.
- Unit economics *(App Economy)* — gross margin, margin expansion with scale, **Rule of 40**,
  **net revenue retention ≥120%** for software; explicit **SBC/dilution** scrutiny.
- Management & capital allocation — owner-operator, skin in the game, value-unlocking.

**Stage 3 — Valuation** *(Valuation agent)* → an **expected 5-yr IRR/EV** and a **buy-below price**
- **Reverse DCF**: back out implied growth/returns, test feasibility *(MBI, Speedwell)*.
- **Bond-yield-anchored IRR hurdle** (~6–7% floor; equity must beat the company's debt) *(MBI)*.
- **Margin of safety %** = (intrinsic value − price) / intrinsic value *(Oguz/Graham)*.
- **Stage-based multiple selection** *(App Economy)* — EV/Revenue or EV/Gross-Profit for
  scalers; EV/FCF or EV/EBITDA for profitable compounders; forward multiples.

**Stage 4 — Red Team / Downside** *(Red Team agent)* → a **bear case + invalidation markers**
- **Forensic red-flag scan**: receivables >15% of sales, inventory growing faster than sales,
  margins implausibly above peers, SBC/dilution, leverage, governance flags.
- Explicit thesis-killers + the **downside floor**.
- Pre-set **invalidation markers** (the future data points that would prove the thesis wrong —
  guards against thesis drift, Morris).
- Asymmetry check: is upside ≫ downside? If not, kill it.

**Stage 5 — Edge Gate** *(Behavioral/Edge agent)* → pass/fail "is this really mispriced?"
- Is there a real **analytical × behavioral** edge? *(Oguz)*
- **Time-arbitrage**: does it pay off over years, so the crowd ignores it (the mispricing
  source)? Is there forced selling / panic / euphoria-driven neglect?
- Contrarian check: is the market "unduly discounting the future"? Are we at an extreme?

**Stage 6 — Portfolio Construction & Sizing** *(Risk/PM agent)* → a **position size + entry plan**
- **Morris 4-variable sizing rubric**: 5-yr expected return × moat durability × profitability
  predictability × management quality → conviction-weighted size for the $10k book.
- **Start small; pre-plan add-on levels** (validated + price still lagging) *(Oguz)*.
- Concentration target ~8–15 names; single-name risk cap; asymmetry-weighted.
- **Pre-arm two sell rules**: (a) upside capped vs position → trim & reallocate to better
  optionality *(Oguz/InPost)*; (b) **thesis cracks** → exit *(Oguz/Hims, Morris)*.

**Stage 7 — Synthesis** *(Portfolio Manager orchestrator — Claude Code)*
- Rank ideas by **expected value × conviction × asymmetry**.
- Produce the **morning briefing**, each idea carrying: 1-line thesis + detail; the secular/edge
  "why now"; Quality Score; valuation & buy-below; bear case + invalidation markers; suggested
  entry zone & size.
- Update the **watchlist**: track live theses, flag entry-level hits and thesis-changing news.

---

## 4. The Agents (personas) — mapped to the funnel

| Agent | Stage | Encodes |
|---|---|---|
| **Scout swarm** (6 sourcing patterns) | 1 | Citrini, Oguz, Slegers, Waller, Walker, App Economy |
| **Moat / Quality Analyst** | 2 | Oguz 5-step moat, Slegers Quality Score, MBI, App Economy |
| **Valuation Analyst** | 3 | MBI reverse-DCF + IRR hurdle, Oguz MoS, App Economy multiples |
| **Red Team / Forensic** | 4 | Short-seller red flags, Morris invalidation markers |
| **Edge Gate (Behavioral)** | 5 | Oguz analytical×behavioral, time-arbitrage |
| **Risk & Portfolio Manager** | 6–7 | Morris 4-var sizing, Oguz start-small/sell-rules |
| **Orchestrator = Claude Code** | all | Runs the funnel, spawns agents, writes the briefing |

**Engineering lenses applied throughout (best-practice guardrails):** AI Engineer (cost-aware
model routing — cheap models for screening breadth, Opus for synthesis depth; reproducible,
logged runs), Hedge-Fund Manager (risk-first sizing, written process), Market Researcher
(point-in-time data to avoid **look-ahead bias**; every claim cited & dated), Designer
(glanceable dashboard — opportunities surface in <30s each morning).

---

## 5. Architecture

```
   Scheduler (GitHub Action cron, each morning)
                 │
                 ▼
   CLAUDE CODE  (orchestrator) ── spawns persona agents (Claude Agent SDK / subagents)
                 │
   ┌─────────────┼───────────────────────────────┐
   ▼             ▼                                ▼
 DATA LAYER (Python)     RESEARCH AGENTS (the funnel)     STORE (git-tracked)
 • FMP / Financial         scout → quality → value →       • universe + fundamentals
   Datasets API            red-team → edge → size → PM     • theses + watchlist
   (fundamentals,        • Bigdata.com MCP (news,          • portfolio + trade log
   prices, earnings,       sentiment, events,             • run history (SQLite/JSON)
   screener)               filings, transcripts)            = the track-record dataset
 • free supplements
   (Finnhub/AlphaVantage)
                 │
                 ▼
        DELIVERY: dated markdown report  →  WEB DASHBOARD (Next.js → Vercel)
   today's opportunities · conviction/EV · thesis + bear case + invalidation ·
   watchlist w/ entry levels · portfolio tracker · research history
```

- **Backend / agents:** Python (domain standard; matches the 50k-star reference impl).
- **Data stack (~$100–200/mo):** **FMP (Financial Modeling Prep) as the recommended primary
  feed** — broadest small/mid-cap coverage + a built-in stock **screener** endpoint (critical for
  Stage 1), fundamentals, prices, earnings; ~$50/mo Premium leaves budget headroom. (Financial
  Datasets API is the fallback; we validate FMP's small/mid-cap coverage on the free tier in
  Phase 1 before paying.) **Bigdata.com MCP** (already connected) supplies the unstructured/
  thematic edge — news search, sentiment, events calendar, filings & transcripts — and powers the
  thematic, contrarian, and red-team agents. Finnhub/Alpha Vantage as free redundancy.
- **Frontend:** Next.js → Vercel. **Scheduling:** GitHub Action cron. **Storage:** git-tracked
  SQLite + JSON so every run/thesis/trade is versioned and auditable (and feeds Phase 5 evals).
- **LLM:** Claude — Opus for deep synthesis, Sonnet/Haiku for bulk screening (cost-aware).

---

## 5b. Repo structure & build specifics

```
hedge-fund/
├── README.md                  # what it is + how to run
├── CLAUDE.md                  # house rules for the orchestrator (the §2 principles, guardrails)
├── pyproject.toml             # Python deps (managed with uv or poetry)
├── .env.example               # FMP_API_KEY, ANTHROPIC_API_KEY, etc. (never commit real keys)
├── methodology/               # §8 knowledge base — one .md per master, loaded into agent prompts
├── src/
│   ├── data/                  # FMP + Bigdata.com clients, point-in-time loaders, caching
│   ├── universe/              # broad US universe builder + filters
│   ├── scouts/                # Stage 1 — 6 sourcing patterns (thematic, transplant, quality,
│   │                          #   hidden-gem, special-sits, contrarian)
│   ├── agents/                # Stages 2–6 — quality, valuation, red_team, edge_gate, risk_pm
│   ├── orchestrator/          # Stage 7 — runs the funnel, writes the briefing
│   ├── store/                 # SQLite + JSON: theses, watchlist, portfolio, run history
│   └── report/                # dated markdown briefing generator
├── reports/                   # YYYY-MM-DD.md briefings (git-tracked history)
├── web/                       # Phase 4 — Next.js dashboard (Vercel)
└── .github/workflows/         # Phase 3 — scheduled daily run (cron)
```

**Agent implementation:** each agent = a Claude call with (a) the relevant `methodology/` context,
(b) structured-output schema (so scores/IRR/sizing are machine-readable, not prose), (c) cited,
dated evidence from FMP + Bigdata.com. Cost-aware routing: Haiku/Sonnet for breadth (Stage 1
screening across the universe), Opus for depth (Stages 3, 5, 7). Every run is logged to `store/`
for the Phase-5 track record. Look-ahead-bias guard: data loaders are point-in-time only.

## 5c. Web dashboard design (the daily surface)

The dashboard is the product the user touches every morning — **investor-grade, updated
daily**, built for three jobs: *delve deeper on a stock*, *see what each persona returned*, and
*full traceability* from headline → stock → agent → evidence.

**Confirmed design language (from user):**
- **Dark "modern terminal"** — Bloomberg-meets-Linear: monospace numerics, color-coded
  conviction (green/amber/red), score gauges & moat radars, clean typographic hierarchy.
- **Balanced-modern density** — data-rich but breathable; deep analysis without fatigue.
- **Side-by-side "Analyst Desk"** — every persona's verdict visible at once to spot agreement/
  disagreement at a glance.
- **Both chart types** — TradingView lightweight-charts candlesticks (volume, support/resistance
  + entry-zone / buy-below bands) for timing, *plus* Tremor fundamental-overlay charts (price vs
  north-star fundamentals) for the thesis.

**Stack:** Next.js + **shadcn/ui** (vendored, fully owned components) + **Tremor** (Vercel-owned;
35+ chart/KPI components) for analytics + **TradingView lightweight-charts** for price. Tailwind,
dark theme. **Statically generated from each daily run's output** (the briefing JSON + `store/`),
so it's fast, cheap, and every page is a pure function of the audited run data.

**Screens (information architecture):**
1. **Today (home / Morning Briefing)** — market-regime + active-themes strip, portfolio P&L
   snapshot, "N new ideas today"; then ranked **opportunity cards** (conviction × EV ×
   asymmetry): ticker, sparkline, 1-line thesis, conviction gauge, upside/downside/asymmetry,
   originating scout badge, entry zone, suggested size; plus a watchlist-alerts panel.
2. **Stock Deep-Dive `/stock/[ticker]`** — the core surface:
   - Header: candlestick chart with entry-zone & buy-below bands, key stats, conviction badge.
   - Thesis & "why now" (secular / edge narrative).
   - **The Analyst Desk** — one panel per persona (Scout · Moat/Quality · Valuation · Red Team ·
     Edge Gate · Risk/PM), each with verdict, score, **full reasoning, and cited dated sources**.
     Moat → 5-dimension radar + Quality Score gauge; Valuation → reverse-DCF implied-vs-achievable
     growth, IRR, margin of safety, buy-below; Red Team → bear case + red-flag checklist
     (pass/fail) + invalidation markers.
   - Financials (ROIC, growth, Rule of 40, NRR, FCF) with **price-vs-fundamentals overlay**;
     news/sentiment timeline (Bigdata.com); **thesis history** — how each persona's verdict
     evolved across daily runs.
3. **Themes & Outlook** — Citrini-style tracker: active secular themes, status, 1st/2nd-order
   beneficiaries, linked stocks, current exposure.
4. **Watchlist** — tracked theses, entry levels, alert status.
5. **Portfolio & Track Record** — positions vs targets, P&L, realized-vs-predicted, hit-rate,
   conviction-calibration curve.
6. **Research Log** — every daily run as a full audit trail; click any recommendation → the exact
   agent outputs + evidence that produced it.

**Traceability model (first-class requirement):** every score and claim links to its source
(filing / news / transcript + date); every verdict exposes its reasoning chain; the path
*briefing → stock → persona → evidence* is navigable, and thesis history adds the time axis. The
`store/` run history is the backing audit log.

---

## 6. Roadmap

- **Phase 0 — Ideation & scaffolding** *(this plan)* — repo structure, README/CLAUDE.md, this
  methodology doc committed, secrets template, deps.
- **Phase 1 — Data layer + Scout screens** — wire FMP/Financial Datasets + Bigdata.com; broad-
  universe loader + the Stage-1 sourcing screens → daily candidate list. *Verify:* run screens,
  eyeball candidates, spot-check fundamentals.
- **Phase 2 — The funnel (agents 2–7)** — quality → value → red-team → edge → size → PM
  synthesis → **dated markdown briefing**. *Verify:* generate a real briefing; sanity-check it
  against the MU-style pattern.
- **Phase 3 — Watchlist monitor + portfolio tracker + scheduling** — track live theses, alert
  on entry levels/news; portfolio + trade log; GitHub Action cron. *Verify:* end-to-end morning
  run on a schedule.
- **Phase 4 — Web dashboard** — Next.js on Vercel rendering opportunities, thesis+bear case,
  watchlist, portfolio, history. *Verify:* preview deploy, open it like a real morning.
- **Phase 5 — Track record & tuning** — calibration/backtest harness; measure hit-rate, R:R, EV;
  tune the Scout weights and agent prompts against realized outcomes.

---

## 7. Verification (how we know it works)

- **Phase 1:** screens produce a non-empty, sane candidate list; spot-check tickers vs a public source.
- **Phase 2:** full briefing for a known name renders thesis, moat/quality score, reverse-DCF
  buy-below, bear case + invalidation markers, entry zone & size — all cited and dated.
- **Phase 3:** scheduled job fires; watchlist alerts trigger on a contrived entry-level hit; trade log updates.
- **Phase 4:** Vercel preview loads; today's report renders.
- **Ongoing:** run-history store accumulates predictions for the Phase-5 track-record review.

---

## 8. Methodology source library (the system's knowledge base)

The agents' prompts encode these writers' techniques; this list also seeds a `methodology/`
knowledge folder. **All performance figures are self-reported/unverified unless noted.**

- **Oguz Erkan — Capitalist Letters** *(user's favorite)*: asymmetry ("heads we win…"), edge =
  analytical×behavioral, 5-step moat analysis, DCF + margin of safety, start-small + conviction
  sizing, two sell rules (capped-upside / thesis-crack), proven-model-in-new-market pattern.
- **Citrini Research** *(closest to user's MU style)*: narrative → thematic **basket** of
  beneficiaries; hunt **second-order** effects; factor-neutralize to isolate selection alpha.
- **Compounding Quality (Slegers)**: ~150-name quality universe, **13-criteria + 15-metric
  Quality Score /10**, ROIC north star, owner ≥10%, reverse-DCF with ≥10% expected-return hurdle.
- **Best Anchor Stocks (Leandro)**: "anchor stocks" easy to hold 10+ yrs; reverse-DCF-first;
  volatility treated as real risk; sell only on broken thesis.
- **App Economy Insights (Eric)**: business-model-first; **Rule of 40**, **NRR ≥120%**, "6
  charts before you buy," SBC/dilution scrutiny; plot price vs north-star fundamentals, buy divergence.
- **MBI Deep Dives (Al-Rezwan)**: reverse-DCF "what must be true"; **bond-yield-anchored IRR
  hurdle** (~6–7%); **moderate growth > hypergrowth**; concentrated ~10–20 names.
- **TSOH (Alex Morris)**: "wait for your pitch"; **4-variable position-sizing rubric**; top-5
  >60%; "letting winners run" / beware thesis drift.
- **Yet Another Value (Andrew Walker)**: special situations; **forced selling as a buy signal**;
  spinoffs; "buy the better business in the spin"; downside-first.
- **Speedwell Research**: extreme-depth primary research; "camera focusing its lens";
  **counterfactual** interrogation of management claims; reverse-DCF.
- **Hidden Gems / Plural (Chris Waller)** *(real fund record)*: small-cap "sleuthing" — ~20
  expert calls before buying; niche leaders at 15–20% ROIC / ~10–13× earnings; 7–8 names, 3–5 yr.
- **The Wolf of Harcourt Street**: GARP/Lynch for platforms; inverse-DCF; full transparency.
- **Rijnberk InvestInsights**: long-only quality+GARP; semis/fintech specialism; 3-pillar (moat,
  financials, growth).
- **From 0 to 1 (Giuliano Mana)**: Terry-Smith disciple; the **"reinvestment moat"**; returns
  from compounding, not re-rating.
- **Doomberg**: energy/commodities macro lens (theme input).
- **Forensic short-seller red flags**: receivables/inventory vs sales, peer-anomalous margins,
  governance — powers the Red Team.

*Branding note:* Bigdata.com (https://bigdata.com) is the unstructured-data provider.

---

## 9. Open items to confirm as we build (not blockers)

- Final primary feed: **FMP vs Financial Datasets API** (decide in Phase 1 on small/mid-cap coverage).
- Exact concentration/position rules (max % per name, max # open ideas) — codify with user in Phase 2.
- Whether to add **crypto** later (Crypto.com data MCP available).
- Product name (working codename "Bear Stearns").
