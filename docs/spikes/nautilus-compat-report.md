# Nautilus 1.231.0 compatibility spike — report

**Date:** 2026-09-22  
**Pin:** `nautilus_trader==1.231.0` (ADR 0002)  
**Python:** 3.12 Windows cp312 wheel  
**Env:** `docs/spikes/nautilus-1.231.0/.venv` (gitignored)

## Decision

**Proceed with NautilusTrader 1.231.0 as the execution-engine candidate for the paper vertical slice.**

TSD owns: target intents, proposals/approvals, command identity map, React workbench, agent tools.  
Nautilus owns: backtest/sim matching, order lifecycle, positions/P&L inside the engine runtime.

Do **not** rebuild a custom OMS or paper matcher. The SQLite paper bridge is a **TSD application-layer** demo until the Nautilus worker is wired for live process control.

## Results matrix

| ID | Check | Status | Evidence |
|---|---|---|---|
| B1 | Exact version pin | PASS | ADR 0002 |
| B2 | Isolated install + import | PASS | venv wheel |
| B3 | Official quickstart unchanged | DEFERRED | Docs quickstart is **2.x**; used 1.x BacktestEngine instead |
| B4 | Local paper/sim one instrument | PASS | `demo_backtest_target.py` |
| B5 | TargetPositionIntent adapter | PASS | `target_position.py` + bridge `planning.py` |
| B6 | 0.18→0.20 ⇒ BUY 0.02 → net 0.20 | PASS | delta + backtest |
| B7 | Deterministic plan parity | PASS | `test_fault_matrix.py::test_parity_*` |
| B8 | Fault matrix | PASS | duplicate/reversal/weight/stale/max qty/kill switch |
| B9 | Restart / no duplicate | PASS | `demo_idempotency.py` + bridge store tests |
| B10 | Decision matrix | PASS | this document |

## What Nautilus provides (verified)

- `BacktestEngine`, simulated venue fills, positions/fills reports
- Strategy + `order_factory.market` submission
- BTCUSDT test instrument helper

## What TSD must still build / integrate

| Need | Owner |
|---|---|
| Propose/approve agent tools | TSD bridge API (done paper stub) |
| Command ID ↔ engine OID persistence | TSD store (SQLite MVP; Postgres later) |
| Wire React to engine events (not only paper SQLite) | Phase C continue |
| Nautilus worker process + event adapter | Next implementation slice |
| Weight/notional FX rules | Later |
| Live venue certification | After paper soak |

## Hummingbot

Not required for MVP while Nautilus covers backtest + sim + IB/crypto adapters. Revisit only if crypto-ops product priorities change.

## Commands

```powershell
cd docs/spikes/nautilus-1.231.0
.\.venv\Scripts\python.exe demo_delta.py
.\.venv\Scripts\python.exe demo_backtest_target.py
.\.venv\Scripts\python.exe demo_idempotency.py
.\.venv\Scripts\python.exe -m pytest test_fault_matrix.py ../../backend/tests -q --import-mode=importlib
```

## Safety

Live trading remains disabled. Prototype broker routes stay fail-closed.
