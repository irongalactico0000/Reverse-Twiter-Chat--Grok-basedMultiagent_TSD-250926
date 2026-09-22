"""Simple server-side risk gates for the paper vertical slice."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from target_position import DerivedOrderPlan


@dataclass(frozen=True, slots=True)
class RiskDecision:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    modified_quantity: Decimal | None = None


def evaluate_plan(
    plan: DerivedOrderPlan,
    *,
    max_order_qty: Decimal | None = None,
    max_abs_position: Decimal | None = None,
    market_data_age_ms: int | None = None,
    max_market_data_age_ms: int | None = None,
    kill_switch: bool = False,
) -> RiskDecision:
    reasons: list[str] = []

    if kill_switch:
        reasons.append("kill_switch_engaged")

    if plan.side != "FLAT" and max_order_qty is not None and plan.quantity > max_order_qty:
        reasons.append(f"max_order_qty_exceeded:{plan.quantity}>{max_order_qty}")

    if max_abs_position is not None:
        projected = abs(plan.target_quantity)
        if projected > max_abs_position:
            reasons.append(f"max_abs_position_exceeded:{projected}>{max_abs_position}")

    if (
        market_data_age_ms is not None
        and max_market_data_age_ms is not None
        and market_data_age_ms > max_market_data_age_ms
    ):
        reasons.append(f"stale_market_data:{market_data_age_ms}ms")

    return RiskDecision(accepted=len(reasons) == 0, reasons=reasons)
