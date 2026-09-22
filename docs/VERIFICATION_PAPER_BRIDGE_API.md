# Paper bridge API verification (2026-09-22)

**Verdict: PASS** — API end-to-end paper flow verified with real Nautilus subprocess (no live orders).

## Runtime

- Entry: `backend/back-end/paper_app.py` (slim FastAPI; no google-adk)
- Venv: `backend/.venv` (fastapi + uvicorn)
- Nautilus: `docs/spikes/nautilus-1.231.0/.venv` via `TSD_NAUTILUS_PYTHON`
- Port: `127.0.0.1:8765` (8000 was occupied)
- Env:

```text
TRADING_API_TOKEN=paper-verify-token
TRADING_MUTATIONS_ENABLED=true
TRADING_REQUIRE_AUTH_FOR_READS=true
TSD_USE_NAUTILUS_PAPER=true
TSD_REQUIRE_NAUTILUS=true
TSD_NAUTILUS_PYTHON=<spike-venv>/python.exe
TSD_BRIDGE_DB=backend/.verify-bridge.sqlite
PYTHONPATH=backend/back-end
```

## Results

| Check | Result |
| --- | --- |
| `GET /api/v1/bridge/safety` | `live_trading_allowed: false`, `mode: paper`, `mode_authority: server` |
| `POST propose_target` 0.18→0.20 | `BUY 0.02`, status `proposed` |
| `POST approve` | `executed_paper`, position `0.200000` |
| Event `paper.filled.execution_engine` | **`nautilus_trader_paper_runner`** (not `ledger_sim` / `plan_only_fallback`) |
| Kill switch propose | `risk_rejected` / `kill_switch_engaged` |
| Kill switch approve | `risk_rejected` / `kill_switch_engaged` |
| Idempotency (same fingerprint) | Reuses `tsd_command_id`; no second `paper.filled` |
| Restart + re-approve | Same command id; `paper.reused_command` only; fills count unchanged |

## Start command (PowerShell)

```powershell
cd C:\Users\user\Multiagent_TSD-250926\backend
$env:PYTHONPATH = (Resolve-Path .\back-end).Path
$env:TRADING_API_TOKEN = 'paper-verify-token'
$env:TRADING_MUTATIONS_ENABLED = 'true'
$env:TRADING_REQUIRE_AUTH_FOR_READS = 'true'
$env:TSD_USE_NAUTILUS_PAPER = 'true'
$env:TSD_REQUIRE_NAUTILUS = 'true'
$env:TSD_NAUTILUS_PYTHON = (Resolve-Path ..\docs\spikes\nautilus-1.231.0\.venv\Scripts\python.exe).Path
$env:TSD_BRIDGE_DB = (Join-Path (Get-Location) '.verify-bridge.sqlite')
.\.venv\Scripts\python.exe -m uvicorn paper_app:app --host 127.0.0.1 --port 8765
```

## Still out of scope / not runtime-verified here

- CAE chat → `trading_proposal_agent` → React bridge panel (source wiring present; UI not driven in this run)
- Live trading (correctly disabled)

## Hardening applied during unblock

- `TSD_REQUIRE_NAUTILUS` (default true when Nautilus paper env is on): reject approve if worker returns `plan_only_fallback`
- Dual import path in `trading_bridge/api.py` for `PYTHONPATH=back-end`
- `paper_app.py` slim entrypoint; `back-end/__init__.py` no longer eagerly imports google-adk agents
