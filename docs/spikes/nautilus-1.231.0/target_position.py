"""TSD TargetPositionIntent → order delta (engine-agnostic).

Normal alpha strategies emit targets. OMS/EMS derives the delta order.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal


class TargetType(str, Enum):
    QUANTITY = "quantity"
    WEIGHT = "weight"
    NOTIONAL = "notional"


@dataclass(frozen=True, slots=True)
class TargetPositionIntent:
    instrument_id: str
    target_type: TargetType
    target_value: Decimal
    strategy_id: str = "spike"
    strategy_version: str = "0.0.0"
    account_scope: str = "paper"
    currency: str | None = None
    reason: str = ""
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class DerivedOrderPlan:
    instrument_id: str
    side: Literal["BUY", "SELL", "FLAT"]
    quantity: Decimal
    current_quantity: Decimal
    target_quantity: Decimal
    reason: str


def quantity_delta(
    *,
    instrument_id: str,
    current_quantity: Decimal,
    target_quantity: Decimal,
    reason: str = "",
) -> DerivedOrderPlan:
    """Derive a signed delta order from current → target quantity."""
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


def plan_from_intent(
    intent: TargetPositionIntent,
    *,
    current_quantity: Decimal,
    portfolio_equity: Decimal | None = None,
    mark_price: Decimal | None = None,
) -> DerivedOrderPlan:
    """Normalize TargetPositionIntent into a quantity delta plan."""
    if intent.target_type is TargetType.QUANTITY:
        target_qty = intent.target_value
    elif intent.target_type is TargetType.WEIGHT:
        if portfolio_equity is None or mark_price is None or mark_price == 0:
            raise ValueError("weight targets require portfolio_equity and mark_price")
        target_notional = portfolio_equity * intent.target_value
        target_qty = target_notional / mark_price
    elif intent.target_type is TargetType.NOTIONAL:
        if mark_price is None or mark_price == 0:
            raise ValueError("notional targets require mark_price")
        target_qty = intent.target_value / mark_price
    else:
        raise ValueError(f"unsupported target_type: {intent.target_type}")

    return quantity_delta(
        instrument_id=intent.instrument_id,
        current_quantity=current_quantity,
        target_quantity=target_qty,
        reason=intent.reason,
    )
