# NautilusTrader 1.231.0 spike environment

Pinned per `docs/adr/0002-nautilus-version-pin.md`.

## Setup

```powershell
cd docs/spikes/nautilus-1.231.0
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt requests pandas
```

Official examples need test CSVs next to the package:

` .venv/Lib/site-packages/tests/test_data/truefx/audusd-ticks.csv`
` .venv/Lib/site-packages/tests/test_data/short-term-interest.csv`

(copied from GitHub `v1.231.0` tag; also mirrored under `./test_data/`).

## Progress

| Task | Status | Evidence |
|---|---|---|
| B1 pin | Done (ADR 0002) | `nautilus_trader==1.231.0` |
| B2 install | Done | Import works on Windows cp312 |
| B3 official backtest | **PASS** | `official_examples/fx_ema_cross_audusd_ticks.py` exit 0; `b3_fx_ema_cross_audusd_ticks.log` |
| B4 paper SIM | **PASS (SIM cash)** | B6 uses `AccountType.CASH` + `OmsType.NETTING` on BINANCE SIM |
| B5–B6 target→delta | **PASS** | `b6_target_position_demo.py` + `tests/test_target_position.py` |
| B7 parity manifest | **PASS** | `artifacts/b7_parity_manifest.json` |
| B8 fault matrix | **PASS** | `tests/test_b7_b9_matrix.py` |
| B9 restart / idempotency | **PASS** | command map in tests |
| B10 compat report | **PASS** | `docs/spikes/nautilus-compat-report.md` |

### B6 proof (recorded)

```
current_before_target: 0.180000
target: 0.20
derived_side: BUY
derived_qty: 0.020000
target_client_order_id: tsd-cmd-b6-001
final_position: 0.200000
nautilus_version: 1.231.0
instrument: BTCUSDT.BINANCE
```

Run:

```powershell
.\.venv\Scripts\python.exe .\b6_target_position_demo.py
.\.venv\Scripts\python.exe -m pytest .\tests\test_target_position.py -q
```

Do **not** enable live trading. Do **not** rebuild a custom OMS.
