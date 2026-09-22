"""Paper target-position job runner (Phase C2).

Accepts TargetPositionIntent-shaped requests, enforces command idempotency via
CommandIdentityStore, runs a short Nautilus SIM backtest job, returns evidence.

This is intentionally a job runner (not a long-lived live node) for the first
vertical slice. Live trading is never enabled here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from tsd_bridge.command_store import CommandIdentity, CommandIdentityStore, JsonCommandIdentityStore
from tsd_bridge.harness import run_scenario


@dataclass(frozen=True, slots=True)
class PaperTargetRequest:
    tsd_command_id: str
    deployment_id: str
    seed_quantity: str = "0.18"
    target_quantity: str = "0.20"
    instrument: str = "BTCUSDT.BINANCE"


@dataclass(frozen=True, slots=True)
class PaperTargetResult:
    accepted: bool
    duplicate: bool
    status: str
    evidence: dict
    identity: CommandIdentity


class PaperTargetRunner:
    def __init__(self, store: CommandIdentityStore):
        self._store = store

    def run(self, request: PaperTargetRequest) -> PaperTargetResult:
        pending = CommandIdentity(
            tsd_command_id=request.tsd_command_id,
            deployment_id=request.deployment_id,
            status="accepted",
        )
        inserted, current = self._store.put_if_absent(pending)
        if not inserted:
            return PaperTargetResult(
                accepted=False,
                duplicate=True,
                status="duplicate",
                evidence={"existing": current.engine_client_order_id, "status": current.status},
                identity=current,
            )

        result = run_scenario(
            "b6",
            seed=request.seed_quantity,
            target=request.target_quantity,
            tsd_command_id=request.tsd_command_id,
        )
        # Prefer the TSD command id as client order id when plan_to_market_order set it.
        engine_oid = request.tsd_command_id
        if engine_oid not in result.orders_submitted and result.orders_submitted:
            engine_oid = result.orders_submitted[-1]

        filled = CommandIdentity(
            tsd_command_id=request.tsd_command_id,
            deployment_id=request.deployment_id,
            engine_client_order_id=engine_oid,
            broker_order_id=None,  # SIM has no external broker id
            status="filled" if result.final_position == Decimal(request.target_quantity) else "submitted",
        )
        self._store.update(filled)
        return PaperTargetResult(
            accepted=True,
            duplicate=False,
            status=filled.status,
            evidence={
                "final_position": str(result.final_position),
                "plans": result.evidence.get("plans", []),
                "orders_submitted": result.orders_submitted,
                "instrument": request.instrument,
                "live_trading": False,
            },
            identity=filled,
        )


def default_runner(data_dir: Path | None = None) -> PaperTargetRunner:
    root = data_dir or Path(__file__).resolve().parents[1] / "artifacts"
    return PaperTargetRunner(JsonCommandIdentityStore(root / "command_identity.json"))
