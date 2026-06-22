# App Economy Insights (Eric)

## Core edge
**Business-model-first** analysis of consumer/software platforms, with a sharp eye on unit
economics and a "buy the divergence between price and north-star fundamentals" discipline.

## Distinctive techniques (encode these)
- **Rule of 40** (revenue growth % + FCF/operating margin % ≥ 40) for scalers.
- **Net revenue retention ≥ 120%** for software — the cleanest signal of a switching-cost moat.
- **"6 charts before you buy."** Visualize the core drivers (growth, margins, retention, FCF,
  dilution, valuation) before forming a view.
- **SBC / dilution scrutiny.** Stock-based comp is a real cost; track share-count growth.
- **Stage-based multiple selection.** EV/Revenue or EV/Gross-Profit for early scalers; EV/FCF or
  EV/EBITDA for profitable compounders. Use forward multiples.
- **Price vs north-star fundamentals.** Plot price against the metric that actually drives the
  business; **buy when price diverges below** the fundamental trend.

## How agents use it
- **Quality agent** computes Rule of 40, NRR, and dilution checks (`src.config` thresholds).
- **Valuation agent** picks the stage-appropriate multiple basis.
- **Contrarian / divergence scout** looks for price-vs-fundamental divergence.
- The dashboard's **price-vs-fundamentals overlay** chart is this idea made visual.
