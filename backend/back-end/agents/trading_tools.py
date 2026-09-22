"""Agent-facing trading tools. Proposals only — never place live orders."""
from __future__ import annotations

from decimal import Decimal

from google.adk.tools import FunctionTool

from ..trading_bridge.facade import get_bridge
from ..trading_bridge.models import TargetPositionRequest, TargetType


def propose_target_position(
    instrument_id: str,
    target_value: str,
    current_quantity: str = "0",
    target_type: str = "quantity",
    reason: str = "agent proposal",
) -> dict:
    """Propose a target position for operator approval (paper bridge).

    Does not submit broker orders. Does not enable live trading.
    """
    request = TargetPositionRequest(
        instrument_id=instrument_id,
        target_type=TargetType(target_type),
        target_value=Decimal(target_value),
        current_quantity=Decimal(current_quantity),
        reason=reason,
        strategy_id="cae-agent",
    )
    proposal = get_bridge().propose(request)
    return {
        "proposal_id": proposal.proposal_id,
        "status": proposal.status.value,
        "plan": proposal.plan.model_dump(mode="json"),
        "risk": proposal.risk.model_dump(mode="json"),
        "note": "Await operator approval via /api/v1/bridge/approve before any paper fill.",
    }


def get_paper_portfolio() -> dict:
    """Read paper bridge positions and recent events (read-only)."""
    bridge = get_bridge()
    return {
        "positions": bridge.positions(),
        "events": bridge.events(limit=20),
        "live_trading_allowed": False,
    }


propose_target_position_tool = FunctionTool(propose_target_position)
get_paper_portfolio_tool = FunctionTool(get_paper_portfolio)
