# Cursor agent status — 2026-09-22 (continued without stop)

## Parallel agents

| Agent | Own |
|---|---|
| Claude Code (fugu) | Phase 0, ADRs, plan/DOCX, started `backend/back-end/trading_bridge/*` |
| Cursor (this) | Phase B Nautilus spike B3–B10, spike `tsd_bridge/*`, optional Nautilus hook in facade |

## Completed

- Phase B all PASS — `docs/spikes/nautilus-compat-report.md`
- Spike tests: **14 passed**
- Bridge tests: **4 passed**
- Facade can call Nautilus when `TSD_USE_NAUTILUS_PAPER=true`

## Remaining (next without conflict)

1. React `/trading` → `/api/v1/bridge` (propose/approve/positions/events)
2. Label synthetic broker UI vs bridge paper ledger
3. Backend venv install of nautilus only if enabling `TSD_USE_NAUTILUS_PAPER`
4. Postgres migration later (SQLite MVP is fine for first demo)
