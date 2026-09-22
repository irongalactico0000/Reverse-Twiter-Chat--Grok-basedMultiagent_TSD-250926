"""TSD ↔ Nautilus bridge primitives for the Phase B spike.

Normal strategies emit TargetPositionIntent. This module derives the delta and
asks Nautilus to submit the resulting order. It does not talk to brokers.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity


QuantityKind = Literal["quantity", "weight", "notional"]


@dataclass(frozen=True, slots=True)
class TargetPositionIntent:
    """Application-level target. OMS/EMS turns this into an order."""

    instrument_id: InstrumentId
    target: Decimal
    kind: QuantityKind = "quantity"
    reason: str = ""
    tsd_command_id: str = ""

    def __post_init__(self) -> None:
        if self.kind != "quantity":
            raise NotImplementedError(
                f"kind={self.kind!r} needs FX/valuation rules; spike supports quantity only",
            )


@dataclass(frozen=True, slots=True)
class DerivedOrderPlan:
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    current: Decimal
    target: Decimal
    tsd_command_id: str
    reason: str

    @property
    def is_noop(self) -> bool:
        return self.quantity == 0


def compute_delta(current: Decimal, intent: TargetPositionIntent) -> DerivedOrderPlan:
    """Derive a market order from target − current (signed quantity)."""
    if intent.kind != "quantity":
        raise NotImplementedError(intent.kind)

    delta = intent.target - current
    if delta == 0:
        side = OrderSide.BUY
        qty = Decimal("0")
    elif delta > 0:
        side = OrderSide.BUY
        qty = delta
    else:
        side = OrderSide.SELL
        qty = -delta

    return DerivedOrderPlan(
        instrument_id=intent.instrument_id,
        side=side,
        quantity=qty,
        current=current,
        target=intent.target,
        tsd_command_id=intent.tsd_command_id,
        reason=intent.reason,
    )


def plan_to_market_order(strategy, plan: DerivedOrderPlan, *, precision: int):
    """Build a Nautilus market order from a DerivedOrderPlan (no submit)."""
    if plan.is_noop:
        return None
    qty = Quantity(plan.quantity, precision=precision)
    client_order_id = None
    if plan.tsd_command_id:
        # Keep TSD command id visible on the engine client order id when possible.
        safe = plan.tsd_command_id.replace(" ", "")[:36]
        client_order_id = ClientOrderId(safe)
    return strategy.order_factory.market(
        instrument_id=plan.instrument_id,
        order_side=plan.side,
        quantity=qty,
        client_order_id=client_order_id,
    )
