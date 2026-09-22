# Next Agent TODO — TSD Trading OS Spike

**Repo:** `C:\Users\user\Multiagent_TSD-250926`  
**Authority docs:** `docs/trading-os-engineering-plan.md`, `docs/trading-os-engineering-plan.yaml`  
**Deliverables already done:** engineering plan MD/YAML, diagrams, DOCX/PDF under `docs/generated/`  
**Phase 0–C progress:** containment + Nautilus 1.231.0 spike + paper bridge API/UI + worker stub ingest  
See `docs/PHASE0_CONTAINMENT.md`, `docs/spikes/nautilus-compat-report.md`, `docs/PHASE_C_BRIDGE.md`  
**Do not:** rebuild OMS/paper broker/P&L ledger; enable live trading; commit secrets; maintain parallel `tsd/osm` execution path

---

## Fundamental rules (do not violate)

1. **Normal strategy output = target position, not order.**  
   `TargetPositionIntent` → OMS/EMS derives delta → order.  
   Example: current `0.18` BTC, target `0.20` → derived `BUY 0.02`.
2. **Direct orders** only for specialized execution strategies (`ExecutionIntent`), still through risk + engine.
3. **One execution authority:** adopt NautilusTrader (spike first). TSD owns bridge/UI/agents/approvals.
4. **Live trading stays disabled** until gates in the engineering plan pass.

---

## Phase A — Containment (before coding trading)

| # | Task | Done when |
|---|---|---|
| A1 | `git status --short --branch`; inventory changed/untracked trading files | Inventory saved (or pasted in PR notes) |
| A2 | Scan those files for secrets/API keys before any commit | No secrets staged |
| A3 | Revoke/rotate any exposed credentials; reference env var names only | Remediation noted |
| A4 | Fail-closed trading mutations: real auth or disable write routes; no wildcard CORS for trading | Unauthorized request cannot place/propose trade |
| A5 | Secret scanning / `.gitignore` for env/credential files | Scan/config present |
| A6 | Classify existing `/trading` + `backend/back-end/trading` as **prototype**, keep recoverable | Label in README or ADR |

---

## Phase B — Engine compatibility spike — **COMPLETE (2026-09-22)**

See `docs/spikes/nautilus-compat-report.md`. All B1–B10 PASS. Pytest: 11 passed.

**Do not redo Phase B.** Start at Phase C.

---

## Phase C — TSD bridge + existing UI

| # | Task | Status |
|---|---|---|
| C1 | Command identity persistence | **DONE** — SQLite in `backend/back-end/trading_bridge/store.py` + spike JSON/`c1_command_identity.sql` |
| C2 | propose_target → approve → paper fill API | **DONE** — `/api/v1/bridge/*` (ledger_sim default; optional `TSD_USE_NAUTILUS_PAPER=true`) |
| C3 | Wire React `/trading` to bridge APIs | **DONE** — TargetBridgePanel.tsx + bridgeApi |
| C4 | Server-authoritative Paper/Live capabilities | **TODO** (live still forced false; server should broadcast account capabilities) |
| C5 | Agent propose_target + approval timeline in UI | **DONE** — trading_proposal_agent added to host_agent sub_agents; TargetBridgePanel shows proposals |
| C6 | Kill switch | **DONE** API (`POST /api/v1/bridge/kill_switch`) |

### Optional Nautilus paper execution

```text
TSD_USE_NAUTILUS_PAPER=true
```

Uses `docs/spikes/nautilus-1.231.0/tsd_bridge/paper_runner.py` from `TradingBridge.execute_paper`. Default remains ledger_sim so the API process does not require `nautilus_trader` installed in the backend venv.

---

## Phase D — After first demo (defer)

- Weight/notional targets (AAPL 3%, Samsung KRW notional) only after FX/valuation/lot rules exist  
- Hummingbot only if same target-position + recovery tests beat Nautilus for crypto-only product  
- Direct `ExecutionIntent` behind stricter permissions  
- Live certification after paper soak + reconciliation + two-person gate  

---

## Acceptance demo (single vertical slice)

```text
Authenticated operator or approved agent proposal
  → TargetPositionIntent(BTCUSDT, quantity=0.20)
  → risk check
  → Nautilus derives / submits paper order
  → fill
  → position + P&L update
  → React shows engine-backed records
  → restart does not duplicate
```

---

## Report format for the implementing agent

Return:

1. Pinned engine version + doc URL  
2. Pass/fail matrix for B3–B9  
3. Path to adapter code and tests  
4. Gaps that force TSD custom code (with MVP necessity yes/no)  
5. Recommended next Phase C tasks only  

Do not claim production readiness. Do not enable live.
