# Forensic short-seller red flags

*Not a single author — the accumulated playbook of forensic accounting / activist short research.
Powers the Red Team. The goal is not to short, but to **avoid value traps and frauds** on the long side.*

## Core edge
Most permanent capital loss comes from accounting games, over-earning, or governance rot that was
visible in the statements beforehand. Systematically scan for it.

## Red-flag checklist (encode these; trip => escalate scrutiny / likely kill)
- **Receivables growing faster than sales** (esp. receivables > ~15% of sales) — possible
  channel-stuffing / aggressive revenue recognition.
- **Inventory growing faster than sales** — demand softening or obsolescence risk.
- **Margins implausibly above peers** — unsustainable or mis-stated; demand a mechanism.
- **Stock-based comp / dilution** eroding per-share value; rising share count.
- **Leverage / refinancing risk** — debt walls, covenant pressure, going-concern language.
- **Cash flow diverging from earnings** — net income up while FCF stalls (low earnings quality).
- **Governance flags** — related-party transactions, auditor changes, restatements, insider
  selling clusters, promotional management.

## How agents use it
- **Red Team agent** runs this scan over FMP fundamentals + Bigdata.com filings, emitting a
  `RedFlag` list (name / tripped / detail). Tripped flags feed the bear case and can veto an idea.
