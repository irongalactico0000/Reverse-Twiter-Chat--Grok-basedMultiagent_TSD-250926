# ADR 0001 — Trading engine boundary and target-position semantics

- **Status:** Proposed
- **Date:** 2026-09-22
- **Context:** TSD needs autonomous strategy → execution → portfolio lifecycle without rebuilding a full OMS.

## Decision

1. **Normal strategy output is `TargetPositionIntent`**, not a broker order.
2. **OMS/EMS (adopted engine) derives orders** from target vs current position.
3. **NautilusTrader** is the default engine candidate; pin an exact version after the compatibility spike.
4. **TSD owns** strategy registry, agent proposals/approvals, deployment, React workbench, and the bridge identity map (`tsd_command_id ↔ engine_client_order_id`).
5. **Engine owns** order lifecycle, fills, positions, trading P&L, paper/sandbox matching.
6. **Direct `ExecutionIntent`** is restricted to specialized execution strategies and still passes risk + engine.
7. **Live trading remains disabled** until containment, paper soak, reconciliation, and governance gates pass.

## Consequences

- Do not maintain a second parallel OMS in `tsd/osm` or `backend/back-end/trading` once the bridge works.
- Existing trading prototype stays fail-closed and labeled prototype.
- Weight/notional targets require explicit FX/valuation rules before use.

## References

- `docs/trading-os-engineering-plan.md`
- `docs/NEXT_AGENT_TODO.md`
- DaxAlgo virtual-book / `SetTargetPosition` pattern
