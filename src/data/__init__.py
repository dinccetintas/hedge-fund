"""Data layer — point-in-time clients for FMP and Bigdata.com.

Phase 1 wires these up. The hard rule (see CLAUDE.md): all loaders are **point-in-time** — they
must never return data dated after the decision date being simulated, to avoid look-ahead bias.
"""
