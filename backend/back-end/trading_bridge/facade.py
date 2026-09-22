"""Paper trading bridge facade: propose → approve → risk → idempotent paper fill."""
from __future__ import annotations

import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from .models import (
    ApprovalRequest,
    DerivedPlanView,
    ProposalStatus,
    RiskDecisionView,
    TargetPositionRequest,
    TargetProposal,
    new_id,
    utcnow,
)
from .planning import evaluate_plan, plan_quantity_intent
from .store import BridgeStore


def _default_db_path() -> Path:
    raw = os.getenv("TSD_BRIDGE_DB", "").strip()
    if raw:
        return Path(raw)
    return Path(os.getenv("LOCALAPPDATA", ".")) / "tsd-trading-bridge" / "bridge.sqlite"


class TradingBridge:
    def __init__(self, store: BridgeStore | None = None) -> None:
        self.store = store or BridgeStore(_default_db_path())
        self.kill_switch = os.getenv("TSD_KILL_SWITCH", "false").lower() in {
            "1",
            "true",
            "yes",
        }
        self.max_order_qty = Decimal(os.getenv("TSD_MAX_ORDER_QTY", "10"))
        self.max_abs_position = Decimal(os.getenv("TSD_MAX_ABS_POSITION", "100"))
        self.max_market_data_age_ms = int(os.getenv("TSD_MAX_MD_AGE_MS", "5000"))

    def propose(self, request: TargetPositionRequest) -> TargetProposal:
        plan = plan_quantity_intent(
            instrument_id=request.instrument_id,
            target_type=request.target_type.value,
            target_value=request.target_value,
            current_quantity=request.current_quantity,
            portfolio_equity=request.portfolio_equity,
            mark_price=request.mark_price,
            reason=request.reason,
        )
        risk = evaluate_plan(
            plan,
            max_order_qty=self.max_order_qty,
            max_abs_position=self.max_abs_position,
            kill_switch=self.kill_switch,
        )
        now = utcnow()
        status = (
            ProposalStatus.risk_rejected if not risk.accepted else ProposalStatus.proposed
        )
        proposal = TargetProposal(
            proposal_id=new_id(),
            status=status,
            request=request,
            plan=DerivedPlanView(
                instrument_id=plan.instrument_id,
                side=plan.side,
                quantity=plan.quantity,
                current_quantity=plan.current_quantity,
                target_quantity=plan.target_quantity,
                reason=plan.reason,
            ),
            risk=RiskDecisionView(accepted=risk.accepted, reasons=list(risk.reasons)),
            created_at=now,
            updated_at=now,
        )
        self.store.upsert_proposal(proposal.proposal_id, proposal.model_dump(mode="json"))
        self.store.append_event(
            "proposal.created",
            {"proposal_id": proposal.proposal_id, "status": proposal.status.value},
        )
        return proposal

    def get_proposal(self, proposal_id: str) -> TargetProposal | None:
        raw = self.store.get_proposal(proposal_id)
        return TargetProposal.model_validate(raw) if raw else None

    def list_proposals(self) -> list[TargetProposal]:
        return [TargetProposal.model_validate(p) for p in self.store.list_proposals()]

    def approve(self, body: ApprovalRequest) -> TargetProposal:
        proposal = self.get_proposal(body.proposal_id)
        if proposal is None:
            raise KeyError(f"proposal not found: {body.proposal_id}")
        if proposal.status == ProposalStatus.risk_rejected:
            raise ValueError("cannot approve a risk-rejected proposal")
        if not body.approve:
            proposal.status = ProposalStatus.rejected
            proposal.updated_at = utcnow()
            self.store.upsert_proposal(proposal.proposal_id, proposal.model_dump(mode="json"))
            self.store.append_event(
                "proposal.rejected",
                {"proposal_id": proposal.proposal_id, "note": body.note},
            )
            return proposal

        # Re-run risk at approval time
        plan = plan_quantity_intent(
            instrument_id=proposal.request.instrument_id,
            target_type=proposal.request.target_type.value,
            target_value=proposal.request.target_value,
            current_quantity=proposal.request.current_quantity,
            portfolio_equity=proposal.request.portfolio_equity,
            mark_price=proposal.request.mark_price,
            reason=proposal.request.reason,
        )
        risk = evaluate_plan(
            plan,
            max_order_qty=self.max_order_qty,
            max_abs_position=self.max_abs_position,
            kill_switch=self.kill_switch,
        )
        if not risk.accepted:
            proposal.status = ProposalStatus.risk_rejected
            proposal.risk = RiskDecisionView(accepted=False, reasons=list(risk.reasons))
            proposal.updated_at = utcnow()
            self.store.upsert_proposal(proposal.proposal_id, proposal.model_dump(mode="json"))
            return proposal

        proposal.status = ProposalStatus.approved
        proposal.updated_at = utcnow()
        self.store.upsert_proposal(proposal.proposal_id, proposal.model_dump(mode="json"))
        return self.execute_paper(proposal.proposal_id)

    def execute_paper(self, proposal_id: str) -> TargetProposal:
        proposal = self.get_proposal(proposal_id)
        if proposal is None:
            raise KeyError(f"proposal not found: {proposal_id}")
        if proposal.status not in {ProposalStatus.approved, ProposalStatus.proposed}:
            # Allow direct paper exec only after approve path sets approved
            if proposal.status != ProposalStatus.approved:
                raise ValueError(f"proposal not executable: {proposal.status}")

        req = proposal.request
        fingerprint = (
            f"{req.instrument_id}|{req.target_type.value}|{req.target_value}|"
            f"from:{req.current_quantity}"
        )
        idem = req.idempotency_key or hashlib.sha256(
            f"{req.deployment_id}|{fingerprint}|{proposal.proposal_id}".encode()
        ).hexdigest()

        command_id = str(uuid4())
        cmd, created = self.store.begin_command(
            tsd_command_id=command_id,
            deployment_id=req.deployment_id,
            idempotency_key=idem,
            intent_fingerprint=fingerprint,
        )
        if not created:
            # Restart / duplicate: reuse existing engine id, do not double-fill
            proposal.tsd_command_id = cmd["tsd_command_id"]
            proposal.engine_client_order_id = cmd.get("engine_client_order_id")
            proposal.status = ProposalStatus.executed_paper
            proposal.updated_at = utcnow()
            self.store.upsert_proposal(proposal.proposal_id, proposal.model_dump(mode="json"))
            self.store.append_event(
                "paper.reused_command",
                {
                    "proposal_id": proposal.proposal_id,
                    "tsd_command_id": proposal.tsd_command_id,
                    "engine_client_order_id": proposal.engine_client_order_id,
                },
            )
            return proposal

        # Optional: run Nautilus SIM job when TSD_USE_NAUTILUS_PAPER=true and spike is present.
        # Default remains ledger fill so the FastAPI process does not require nautilus_trader.
        nautilus_evidence = self._try_nautilus_paper(proposal, cmd["tsd_command_id"])

        engine_oid = (
            nautilus_evidence.get("engine_client_order_id")
            if nautilus_evidence
            else f"PAPER-{uuid4().hex[:12]}"
        )
        self.store.mark_command_submitted(
            cmd["tsd_command_id"],
            engine_client_order_id=engine_oid,
            broker_order_id=(
                nautilus_evidence.get("broker_order_id")
                if nautilus_evidence
                else f"SIM-{engine_oid}"
            ),
        )

        # Apply paper fill: set position to target (Nautilus evidence must match)
        target_qty = str(proposal.plan.target_quantity)
        if nautilus_evidence and nautilus_evidence.get("final_position"):
            target_qty = nautilus_evidence["final_position"]
        self.store.set_position(proposal.plan.instrument_id, target_qty)
        proposal.tsd_command_id = cmd["tsd_command_id"]
        proposal.engine_client_order_id = engine_oid
        proposal.status = ProposalStatus.executed_paper
        proposal.updated_at = utcnow()
        self.store.upsert_proposal(proposal.proposal_id, proposal.model_dump(mode="json"))
        self.store.append_event(
            "paper.filled",
            {
                "proposal_id": proposal.proposal_id,
                "side": proposal.plan.side,
                "quantity": str(proposal.plan.quantity),
                "target_quantity": str(proposal.plan.target_quantity),
                "engine_client_order_id": engine_oid,
                "execution_engine": (
                    "nautilus_trader" if nautilus_evidence else "ledger_sim"
                ),
                "nautilus": nautilus_evidence,
            },
        )
        return proposal

    def _try_nautilus_paper(
        self, proposal: TargetProposal, tsd_command_id: str
    ) -> dict | None:
        if os.getenv("TSD_USE_NAUTILUS_PAPER", "false").lower() not in {
            "1",
            "true",
            "yes",
        }:
            return None

        # Prefer spike-venv subprocess so API deps need not include nautilus_trader.
        try:
            from .nautilus_worker import emit_target_cycle, run_as_subprocess, write_events

            out = Path(__file__).resolve().parent / "last_run.jsonl"
            proc = run_as_subprocess(
                current_quantity=str(proposal.request.current_quantity),
                target_quantity=str(proposal.plan.target_quantity),
                tsd_command_id=tsd_command_id,
                out=out,
            )
            events: list = []
            if proc.returncode == 0 and out.is_file():
                for line in out.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    raw = json.loads(line)
                    events.append(raw)
            else:
                # In-process fallback (plan_only if nautilus missing in this interpreter).
                typed = emit_target_cycle(
                    instrument_id=proposal.request.instrument_id,
                    current_quantity=str(proposal.request.current_quantity),
                    target_quantity=str(proposal.plan.target_quantity),
                    deployment_id=proposal.request.deployment_id,
                    tsd_command_id=tsd_command_id,
                )
                write_events(out, typed)
                events = [
                    {
                        "event_type": e.event_type,
                        "payload": e.payload,
                    }
                    for e in typed
                ]

            def _find(et: str) -> dict:
                for e in events:
                    if e.get("event_type") == et:
                        return e.get("payload") or {}
                return {}

            fill = _find("trading.order.filled.v1")
            pos = _find("trading.position.updated.v1")
            planned = _find("trading.target.planned.v1")
            engine = fill.get("engine") or planned.get("engine") or "nautilus_worker"
            return {
                "accepted": True,
                "duplicate": False,
                "status": "filled",
                "final_position": pos.get("quantity") or str(proposal.plan.target_quantity),
                "engine_client_order_id": fill.get("engine_client_order_id", tsd_command_id),
                "broker_order_id": f"SIM-{fill.get('engine_client_order_id', tsd_command_id)}",
                "plans": [planned.get("plan") or {}],
                "jsonl": str(out),
                "engine": engine,
                "subprocess_rc": proc.returncode,
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": "worker_failed", "detail": str(exc)}

    def positions(self) -> list[dict[str, str]]:
        return self.store.list_positions()

    def events(self, limit: int = 100) -> list[dict]:
        return self.store.list_events(limit=limit)

    def set_kill_switch(self, enabled: bool) -> dict:
        self.kill_switch = enabled
        self.store.append_event("kill_switch", {"enabled": enabled})
        return {"kill_switch": self.kill_switch}


_bridge: TradingBridge | None = None


def get_bridge() -> TradingBridge:
    global _bridge
    if _bridge is None:
        _bridge = TradingBridge()
    return _bridge
