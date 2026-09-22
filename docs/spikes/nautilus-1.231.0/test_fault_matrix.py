"""Fault-matrix and parity tests for TargetPositionIntent → delta planning."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from target_position import (  # noqa: E402
    TargetPositionIntent,
    TargetType,
    plan_from_intent,
    quantity_delta,
)


def test_parity_same_inputs_same_plan():
    intent = TargetPositionIntent(
        instrument_id="BTCUSDT.BINANCE",
        target_type=TargetType.QUANTITY,
        target_value=Decimal("0.20"),
    )
    a = plan_from_intent(intent, current_quantity=Decimal("0.18"))
    b = plan_from_intent(intent, current_quantity=Decimal("0.18"))
    assert a == b
    assert a.quantity == Decimal("0.02")
    assert a.side == "BUY"


def test_duplicate_target_is_flat():
    plan = quantity_delta(
        instrument_id="BTCUSDT.BINANCE",
        current_quantity=Decimal("0.20"),
        target_quantity=Decimal("0.20"),
    )
    assert plan.side == "FLAT"
    assert plan.quantity == 0


def test_reversal_long_to_short():
    plan = quantity_delta(
        instrument_id="BTCUSDT.BINANCE",
        current_quantity=Decimal("0.20"),
        target_quantity=Decimal("-0.10"),
    )
    assert plan.side == "SELL"
    assert plan.quantity == Decimal("0.30")


def test_partial_scale_in():
    plan = quantity_delta(
        instrument_id="BTCUSDT.BINANCE",
        current_quantity=Decimal("0.18"),
        target_quantity=Decimal("0.20"),
    )
    assert plan.side == "BUY"
    assert plan.quantity == Decimal("0.02")


def test_weight_target_requires_valuation():
    intent = TargetPositionIntent(
        instrument_id="AAPL.NASDAQ",
        target_type=TargetType.WEIGHT,
        target_value=Decimal("0.03"),
    )
    with pytest.raises(ValueError):
        plan_from_intent(intent, current_quantity=Decimal("0"))


def test_weight_target_computes_quantity():
    intent = TargetPositionIntent(
        instrument_id="AAPL.NASDAQ",
        target_type=TargetType.WEIGHT,
        target_value=Decimal("0.03"),
    )
    plan = plan_from_intent(
        intent,
        current_quantity=Decimal("5"),
        portfolio_equity=Decimal("100000"),
        mark_price=Decimal("150"),
    )
    # 3% of 100k = 3000 / 150 = 20 shares; delta from 5 = +15
    assert plan.target_quantity == Decimal("20")
    assert plan.side == "BUY"
    assert plan.quantity == Decimal("15")


def test_notional_krw_requires_mark():
    intent = TargetPositionIntent(
        instrument_id="005930.KRX",
        target_type=TargetType.NOTIONAL,
        target_value=Decimal("20000000"),
        currency="KRW",
    )
    with pytest.raises(ValueError):
        plan_from_intent(intent, current_quantity=Decimal("0"))


def test_stale_policy_reject_helper():
    from risk_gates import RiskDecision, evaluate_plan

    plan = quantity_delta(
        instrument_id="BTCUSDT.BINANCE",
        current_quantity=Decimal("0.18"),
        target_quantity=Decimal("0.20"),
    )
    decision = evaluate_plan(
        plan,
        max_order_qty=Decimal("0.01"),
        market_data_age_ms=5_000,
        max_market_data_age_ms=1_000,
    )
    assert decision.accepted is False
    assert "stale" in decision.reasons[0] or "max_order" in ",".join(decision.reasons)
