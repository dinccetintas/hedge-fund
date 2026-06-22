"""Report generation — the dated markdown morning briefing.

Phase 2 renders a `Briefing` (src.schemas) into `reports/YYYY-MM-DD.md` via a Jinja2 template:
ranked ideas, each with thesis + why-now, quality score, valuation & buy-below, bear case +
invalidation markers, entry zone & size — all cited and dated. The same `Briefing` JSON is what
the web dashboard (Phase 4) renders, so the markdown and the dashboard never diverge.
"""
