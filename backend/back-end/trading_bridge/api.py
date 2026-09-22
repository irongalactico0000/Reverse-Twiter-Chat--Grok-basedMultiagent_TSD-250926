"""HTTP API for the paper trading bridge (propose_target / approve / positions)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..trading.safety import require_trading_mutation, require_trading_read, trading_safety_status

from .facade import get_bridge
from .models import ApprovalRequest, TargetPositionRequest, TargetProposal

router = APIRouter(prefix="/api/v1/bridge", tags=["Trading Bridge (paper)"])


def _account_capabilities() -> list[dict]:
    """Per-broker capability chips — UI must not invent Full/Data/Live flags."""
    try:
        from ..trading.broker_pool import get_pool

        pool = get_pool()
        return [
            {
                "account_id": info.id,
                "name": info.name,
                "status": str(info.status),
                "supports_orders": info.supports_orders,
                "is_paper": info.is_paper,
                "live_trading": False,  # hard gate until plan gates pass
                "mode": "paper" if info.is_paper else "paper_forced",
            }
            for info in pool.list_brokers()
        ]
    except Exception:  # noqa: BLE001 — capabilities must still return if pool missing
        return []


@router.get("/safety")
async def bridge_safety():
    status = trading_safety_status()
    status["bridge"] = "paper_target_position"
    status["live_trading_allowed"] = False
    status["capabilities"] = {
        "live_trading": False,
        "paper_trading": True,
        "mode": "paper",
        "mode_authority": "server",
        "target_types": ["quantity"],
        "target_types_planned": ["weight", "notional"],
        "execution_engines": ["ledger_sim", "nautilus_paper_job"],
        "nautilus_paper_env": "TSD_USE_NAUTILUS_PAPER",
        "mutations_require_token": True,
        "chart": "/static/chart.html",
        "accounts": _account_capabilities(),
    }
    return status


@router.get("/capabilities")
async def bridge_capabilities():
    """Server-authoritative account/trading capability map for desktop + React."""
    safety = await bridge_safety()
    return safety["capabilities"]


@router.post("/propose_target", response_model=TargetProposal)
async def propose_target(
    body: TargetPositionRequest,
    _: str = Depends(require_trading_mutation),
):
    """Agent/operator tool: create a proposal (not an order)."""
    try:
        return get_bridge().propose(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/proposals", response_model=list[TargetProposal])
async def list_proposals(_: str = Depends(require_trading_read)):
    return get_bridge().list_proposals()


@router.get("/proposals/{proposal_id}", response_model=TargetProposal)
async def get_proposal(proposal_id: str, _: str = Depends(require_trading_read)):
    proposal = get_bridge().get_proposal(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    return proposal


@router.post("/approve", response_model=TargetProposal)
async def approve_proposal(
    body: ApprovalRequest,
    _: str = Depends(require_trading_mutation),
):
    try:
        return get_bridge().approve(body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/positions")
async def bridge_positions(_: str = Depends(require_trading_read)):
    return get_bridge().positions()


@router.get("/events")
async def bridge_events(limit: int = 100, _: str = Depends(require_trading_read)):
    return get_bridge().events(limit=limit)


@router.post("/kill_switch")
async def kill_switch(enabled: bool = True, _: str = Depends(require_trading_mutation)):
    return get_bridge().set_kill_switch(enabled)


@router.post("/ingest_engine_stub")
async def ingest_engine_stub(_: str = Depends(require_trading_mutation)):
    """Run Nautilus worker stub cycle and ingest JSONL events into the paper bridge."""
    from .event_adapter import run_stub_and_ingest

    return run_stub_and_ingest(get_bridge())
