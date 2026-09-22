"""Engine-agnostic target planning + risk (copied semantics from spike)."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True, slots=True)
class DerivedOrderPlan:
    instrument_id: str
    side: Literal["BUY", "SELL", "FLAT"]
    quantity: Decimal
    current_quantity: Decimal
    target_quantity: Decimal
    reason: str


@dataclass(frozen=True, slots=True)
class RiskDecision:
    accepted: bool
    reasons: list[str] = field(default_factory=list)


def quantity_delta(
    *,
    instrument_id: str,
    current_quantity: Decimal,
    target_quantity: Decimal,
    reason: str = "",
) -> DerivedOrderPlan:
    delta = target_quantity - current_quantity
    if delta > 0:
        side: Literal["BUY", "SELL", "FLAT"] = "BUY"
        qty = delta
    elif delta < 0:
        side = "SELL"
        qty = abs(delta)
    else:
        side = "FLAT"
        qty = Decimal("0")
    return DerivedOrderPlan(
        instrument_id=instrument_id,
        side=side,
        quantity=qty,
        current_quantity=current_quantity,
        target_quantity=target_quantity,
        reason=reason,
    )


def plan_quantity_intent(
    *,
    instrument_id: str,
    target_type: str,
    target_value: Decimal,
    current_quantity: Decimal,
    portfolio_equity: Decimal | None,
    mark_price: Decimal | None,
    reason: str,
) -> DerivedOrderPlan:
    if target_type == "quantity":
        target_qty = target_value
    elif target_type == "weight":
        if portfolio_equity is None or mark_price is None or mark_price == 0:
            raise ValueError("weight targets require portfolio_equity and mark_price")
        target_qty = portfolio_equity * target_value / mark_price
    elif target_type == "notional":
        if mark_price is None or mark_price == 0:
            raise ValueError("notional targets require mark_price")
        target_qty = target_value / mark_price
    else:
        raise ValueError(f"unsupported target_type: {target_type}")

    return quantity_delta(
        instrument_id=instrument_id,
        current_quantity=current_quantity,
        target_quantity=target_qty,
        reason=reason,
    )


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
    if max_abs_position is not None and abs(plan.target_quantity) > max_abs_position:
        reasons.append(
            f"max_abs_position_exceeded:{abs(plan.target_quantity)}>{max_abs_position}"
        )
    if (
        market_data_age_ms is not None
        and max_market_data_age_ms is not None
        and market_data_age_ms > max_market_data_age_ms
    ):
        reasons.append(f"stale_market_data:{market_data_age_ms}ms")
    return RiskDecision(accepted=not reasons, reasons=reasons)
