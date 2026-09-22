# Phase 0 containment report — 2026-09-22

## Inventory (git)

Branch: `main...origin/main`

### Modified
- `backend/.env.example` — placeholder broker + trading gate vars (no live secrets)
- `backend/back-end/main.py` — trading router + CORS allowlist
- `backend/pyproject.toml` — alpaca/ib deps
- `frontend/package.json`, `frontend/src/Router.tsx` — `/trading` route
- `tsd/config/auth_config.py`, `tsd/core/types/exchange.py`, `tsd/osm/order_service_manager.py`, `tsd/pyproject.toml`

### Untracked prototype (recoverable; not production)
- `backend/back-end/trading/**` — FastAPI broker pool + direct order routes
- `frontend/src/{apis,components,pages}/trading/**` — React trading workbench prototype
- `tsd/osm/managers/{alpaca,ctrader,interactive_brokers}.py` — OSM manager stubs
- `docs/**`, `tools/generate_trading_plan.py` — engineering plan package

## Secret scan

| Finding | Severity | Action |
|---|---|---|
| No `backend/.env` present on disk | OK | Keep using `.env.example` only |
| `.env.example` placeholders only (`your_*`) | OK | Do not replace with real keys in git |
| `auth/api.py` constant token `1234567890` | Medium | CAE stub auth; trading no longer trusts it. Trading uses `TRADING_API_TOKEN` |
| Hardcoded live API keys in trading/OSM | None found | Continue scanning before any commit |
| CORS `allow_origins=["*"]` + credentials | Fixed | Default localhost allowlist; `*` opt-in |

**Remediation if any real key was ever pasted into chat/shell/history:** rotate Alpaca / cTrader / Google keys at the provider; do not commit rotated values.

## Fail-closed gates applied

| Control | Default | Env |
|---|---|---|
| Trading mutations | **OFF** | `TRADING_MUTATIONS_ENABLED=false` |
| Trading API auth | Required | `TRADING_API_TOKEN` |
| Read auth | ON | `TRADING_REQUIRE_AUTH_FOR_READS=true` |
| Live trading | Always false in safety status | N/A until plan gates pass |
| CORS | Localhost allowlist | `CORS_ALLOW_ORIGINS` |

Public probe: `GET /api/v1/trading/safety` (no secrets).

## Prototype label

`backend/back-end/trading` and frontend `/trading` are **prototypes**. They forward orders too directly to adapters and are superseded by the Nautilus bridge path in `docs/trading-os-engineering-plan.md` / `docs/NEXT_AGENT_TODO.md`.

## README conflict

`tsd/README.md` contained merge conflict markers (`<<<<<<< HEAD`). Resolved by keeping the integration guide content and dropping the empty remote stub.

## Next

Phase B engine spike per `docs/NEXT_AGENT_TODO.md`.

### Progress 2026-09-22 (this session)

- [x] A1 inventory written here
- [x] A2–A3 secret scan (no live keys; rotate if ever pasted outside git)
- [x] A4 fail-closed mutations + token + CORS allowlist
- [x] A5 root `.gitignore` for `.env` / spike venvs
- [x] A6 prototype labels + ADR 0001/0002
- [x] B1 pin `nautilus_trader==1.231.0` (ADR 0002)
- [x] B2 isolated venv install + import smoke
- [x] B4–B6 target-position delta + backtest net 0.20 (`docs/spikes/nautilus-compat-report.md`)
- [x] B7–B10 fault matrix / restart / decision (`docs/spikes/nautilus-compat-report.md`)
- [x] Phase C paper bridge API + React panel (`docs/PHASE_C_BRIDGE.md`)
- [ ] Nautilus worker event adapter (next)
- [ ] CAE agent `propose_target` tool registration
