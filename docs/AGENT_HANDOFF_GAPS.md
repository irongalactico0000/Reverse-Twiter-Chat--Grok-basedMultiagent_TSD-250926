# Agent handoff — detailed gap work (Avalonia + plan leftovers)

**Repo:** `C:\Users\user\Multiagent_TSD-250926`  
**Date:** 2026-09-23  
**Audience:** next coding agent  

This document is the executable gap list the engineering plan was thin on. Prefer this over reinventing converters or Nautilus wiring.

---

## A. Avalonia desktop crash blockers (do first)

### A1. Value converters — **DONE**

Files:

- `desktop/Converters/TsdConverters.cs` — 9 converters
- Registered in `desktop/App.axaml` under `Application.Resources`
- Theme split: `Assets/TsdTheme.axaml` (colors) + `Assets/TsdStyles.axaml` (styles)
- **Build:** `dotnet build desktop/TSD.Desktop.csproj` succeeds (0 errors)

| ResourceKey | Input | Output |
|---|---|---|
| `StatusColorConverter` | broker status string | brush (dot) |
| `BoolToOrderBgConverter` | SupportsOrders | badge bg |
| `BoolToOrderFgConverter` | SupportsOrders | badge fg |
| `BoolToOrderLabelConverter` | SupportsOrders | `Full` / `Data` |
| `RunningBorderConverter` | IsRunning bool | card border |
| `StatusChipBgConverter` | RUNNING/PAUSED/STOPPED | chip bg |
| `StatusChipFgConverter` | status string | chip fg |
| `SignalBgConverter` | LONG/SHORT/FLAT | signal bg |
| `SignalFgConverter` | signal string | signal fg |

AXAML should use: `Converter={StaticResource StatusColorConverter}` (already updated in BrokerStatus + StrategyCatalog).

**Verify:** `dotnet build desktop/TSD.Desktop.csproj` then run; no missing-resource exceptions.

### A2. ViewLocator — **DONE in this session**

`desktop/ViewLocator.cs` now maps:

```text
TSD.Desktop.ViewModels.FooViewModel  →  TSD.Desktop.Views.FooView
TSD.Desktop.ViewModels.MainWindowViewModel → TSD.Desktop.Views.MainWindow
```

Note: `MainWindow.axaml` already embeds child views directly (`v:BrokerStatusView` etc.), so ViewLocator is mainly for any future navigation DataTemplates. Keep the mapping correct anyway.

### A3. `GET /static/chart.html` — **DONE in this session**

- File: `backend/back-end/static/chart.html` (lightweight-charts CDN + synthetic candles)
- Mount: `app.mount("/static", StaticFiles(...))` in `backend/back-end/main.py`
- Desktop URL: `TradingChartViewModel.ChartUrl` → `{TSD_API_URL}/static/chart.html?symbol=BTCUSDT`

**Verify:**

```powershell
# with API running
curl http://localhost:8000/static/chart.html
```

NativeWebView xmlns uses `Avalonia.Controls.WebView` assembly. If build fails on `NativeWebView`, check package docs for Avalonia 12.1 control name (`WebView` vs `NativeWebView`).

### A4. Mac / Linux OutputType — **DONE in this session**

`desktop/TSD.Desktop.csproj`:

```xml
<OutputType Condition="$([MSBuild]::IsOSPlatform('Windows'))">WinExe</OutputType>
<OutputType Condition="!$([MSBuild]::IsOSPlatform('Windows'))">Exe</OutputType>
```

**Agent follow-up on Mac:** `dotnet build` + `dotnet run --project desktop` with `TSD_API_URL` set; WebView may need extra macOS entitlements — document any runtime error.

---

## B. Backend / bridge leftovers (from engineering plan)

### B1. Server-authoritative capabilities — **partially DONE**

- `GET /api/v1/bridge/capabilities`
- Also embedded in `GET /api/v1/bridge/safety` as `capabilities`

Desktop/React **must not** treat a client Paper/Live toggle as authority. Bind UI mode chips to this endpoint.

**Still needed:** Desktop `TradingApiClient` method + banner binding to `capabilities.live_trading` / `paper_trading`.

### B2. Nautilus worker — **job path exists; not a persistent process**

Current:

- Spike: `docs/spikes/nautilus-1.231.0/tsd_bridge/paper_runner.py`
- Facade: `TradingBridge._try_nautilus_paper` when `TSD_USE_NAUTILUS_PAPER=true`
- Stub JSONL: `nautilus_worker_stub.py` / `event_adapter.py`

**Not done (give to agent, ~2–3h):**

1. Subprocess launcher from FastAPI (isolated spike venv python) so backend venv need not install Nautilus.
2. CLI entry: `python -m tsd_bridge.paper_runner --seed 0.18 --target 0.20 --command-id …` printing JSON evidence to stdout.
3. Facade calls subprocess with timeout; on failure fall back to ledger_sim and record `execution_engine` in events.
4. Do **not** start a long-lived live node yet.

Acceptance:

```text
TSD_USE_NAUTILUS_PAPER=true
approve propose 0.18→0.20
→ event paper.filled.execution_engine == nautilus_trader
→ position 0.20
→ duplicate idempotency key does not second-submit
```

### B3. PostgreSQL

Defer until single-worker SQLite paper soak is stable. Migration sketch later: `commands`, `proposals`, `positions`, `events` tables already defined in `BridgeStore`.

### B4. Weight / notional targets

Planning code exists (`plan_quantity_intent`) but capabilities advertise only `quantity`. Enable weight/notional only after FX + mark_price validation UX exists.

### B5. DSM → chart

`chart.html` is synthetic. Next agent should replace bar generation with a WebSocket/SSE from DSM gateway (not yet built). Keep chart.html contract (`?symbol=`) stable.

---

## C. Exact agent tickets (copy/paste)

### Ticket 1 — Avalonia polish QA (1h)

```text
Repo: Multiagent_TSD-250926/desktop
1. dotnet build TSD.Desktop.csproj
2. Fix any NativeWebView type/xmlns issues for Avalonia.Controls.WebView 12.1
3. Run against localhost:8000 with chart.html mounted
4. Confirm broker dots, order badges, strategy chips render (converters)
5. Report any remaining binding errors from Avalonia DevTools
```

### Ticket 2 — Desktop capabilities binding (1h)

```text
Add TradingApiClient.GetCapabilitiesAsync → GET /api/v1/bridge/capabilities
Show live_trading=false / paper_trading=true in MainWindow banner
Never enable a client Live toggle from local state alone
```

### Ticket 3 — Nautilus subprocess paper job (2–3h)

```text
Add docs/spikes/nautilus-1.231.0/tsd_bridge/__main__.py CLI
Facade: if TSD_USE_NAUTILUS_PAPER, spawn spike .venv python -m tsd_bridge ...
Parse JSON evidence; map engine_client_order_id; fall back ledger_sim
Tests: subprocess mocked + optional integration if nautilus installed
```

### Ticket 4 — DSM chart feed (later)

```text
Keep /static/chart.html?symbol=
Add /api/v1/market/bars?symbol=&tf=1m returning JSON bars
chart.html fetch bars instead of synthetic walk
```

---

## D. Do not do

- Do not rebuild OMS / paper matcher
- Do not enable live trading
- Do not commit secrets
- Do not attach raw `send_order` tools to CAE host agent
- Do not replace quantity targets with weight/notional in UI until valuation rules exist

---

## E. Quick verification commands

```powershell
cd C:\Users\user\Multiagent_TSD-250926
dotnet build desktop\TSD.Desktop.csproj
# API
# uvicorn / python -m ... then:
# curl http://localhost:8000/static/chart.html
# curl http://localhost:8000/api/v1/bridge/capabilities
```
