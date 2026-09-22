# Phase C progress — trading bridge

## Done

- `backend/back-end/trading_bridge/` paper facade:
  - `POST /api/v1/bridge/propose_target`
  - `POST /api/v1/bridge/approve`
  - `GET /api/v1/bridge/proposals|positions|events`
  - `POST /api/v1/bridge/kill_switch`
- Idempotent command identity in SQLite (`TSD_BRIDGE_DB`)
- Risk re-check on approve; kill switch; max order/position gates
- React: `bridgeApi`, hooks, `TargetBridgePanel` on `/trading`
- Banner: prototype + live disabled

## Auth to exercise locally

```text
TRADING_API_TOKEN=dev-token
TRADING_MUTATIONS_ENABLED=true
VITE_TRADING_API_TOKEN=dev-token
```

## Not done yet / next slice

- Wire Nautilus **live process** (not only stub JSONL) for continuous paper
- Replace SQLite with PostgreSQL for multi-worker
- Remove synthetic chart fixtures when DSM gateway exists
- Optionally attach `trading_proposal_agent` under host_agent (kept separate so CAE is unchanged)

## Added this session

- `agents/trading_tools.py` + `agents/trading_agent.py` — propose_target / get_paper_portfolio
- `trading_bridge/nautilus_worker_stub.py` + `event_adapter.py`
- `POST /api/v1/bridge/ingest_engine_stub`
