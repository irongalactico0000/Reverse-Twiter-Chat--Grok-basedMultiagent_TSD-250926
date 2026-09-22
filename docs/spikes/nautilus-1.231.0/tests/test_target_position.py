from decimal import Decimal

from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import Venue

from tsd_bridge import TargetPositionIntent, compute_delta


def test_compute_delta_0_18_to_0_20():
    instrument = InstrumentId(Symbol("BTCUSDT"), Venue("BINANCE"))
    intent = TargetPositionIntent(instrument_id=instrument, target=Decimal("0.20"))
    plan = compute_delta(Decimal("0.18"), intent)
    assert plan.side == OrderSide.BUY
    assert plan.quantity == Decimal("0.02")
    assert not plan.is_noop


def test_compute_delta_noop():
    instrument = InstrumentId(Symbol("BTCUSDT"), Venue("BINANCE"))
    intent = TargetPositionIntent(instrument_id=instrument, target=Decimal("0.20"))
    plan = compute_delta(Decimal("0.20"), intent)
    assert plan.is_noop
    assert plan.quantity == 0
