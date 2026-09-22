"""Prove BTCUSDT 0.18 → target 0.20 yields BUY 0.02 (engine-agnostic)."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from target_position import TargetPositionIntent, TargetType, plan_from_intent


def main() -> None:
    intent = TargetPositionIntent(
        instrument_id="BTCUSDT.BINANCE",
        target_type=TargetType.QUANTITY,
        target_value=Decimal("0.20"),
        reason="spike demo",
    )
    plan = plan_from_intent(intent, current_quantity=Decimal("0.18"))
    assert plan.side == "BUY", plan
    assert plan.quantity == Decimal("0.02"), plan
    print("PASS", plan)


if __name__ == "__main__":
    main()
