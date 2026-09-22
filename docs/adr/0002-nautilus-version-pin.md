# ADR 0002 — Pin NautilusTrader for compatibility spike

- **Status:** Accepted for spike (not final production pin until B10 report)
- **Date:** 2026-09-22

## Decision

Pin the **stable** line for the first TSD compatibility spike:

| Field | Value |
|---|---|
| Package | `nautilus_trader` |
| Version | **1.231.0** |
| Python | 3.12–3.14 (`requires-python: >=3.12,<3.15`) |
| Docs | https://nautilustrader.io/docs/latest/ |
| Install (stable) | `pip install nautilus_trader==1.231.0` |
| Alternate index | `https://packages.nautechsystems.io/simple` |

## Why not 2.0.0rcN yet

PyPI also publishes `2.0.0rc1`…`2.0.0rc5`. v2 is a Rust/PyO3 cutover with different packaging/docs than the v1 Cython line. Both import as `nautilus_trader`, so mixing them in one environment is unsafe.

**Spike rule:** use **1.231.0** in an isolated venv first. Only evaluate `2.0.0rc*` in a **second** venv if 1.231.0 fails target-position / paper recovery requirements.

## Matching documentation

Use docs that match the installed version. Prefer the release notes for `v1.231.0` on GitHub when APIs diverge from “latest” docs that may describe v2 RC behavior.

## Spike location

`docs/spikes/nautilus-1.231.0/` (venv gitignored via root `.gitignore` / local `.venv`)

## Exit criteria

See Phase B in `docs/NEXT_AGENT_TODO.md`. Record results in `docs/spikes/nautilus-compat-report.md`.
