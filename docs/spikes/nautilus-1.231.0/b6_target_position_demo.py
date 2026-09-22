"""B5–B6 proof: current 0.18 BTC → target 0.20 → derived BUY 0.02 → fill → position.

Uses Nautilus BacktestEngine + SIM venue only. No live brokers.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarSpecification
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.model.enums import BarAggregation
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

SPIKE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE_ROOT))

from tsd_bridge import TargetPositionIntent, compute_delta, plan_to_market_order  # noqa: E402


class TargetDemoConfig(StrategyConfig, frozen=True):
    instrument_id: object
    bar_type: BarType
    seed_quantity: str = "0.18"
    target_quantity: str = "0.20"
    tsd_command_id: str = "tsd-cmd-b6-001"


class TargetPositionDemoStrategy(Strategy):
    """Seeds a starting position, then applies one TargetPositionIntent."""

    def __init__(self, config: TargetDemoConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.seed_qty = Decimal(config.seed_quantity)
        self.target_qty = Decimal(config.target_quantity)
        self.tsd_command_id = config.tsd_command_id
        self.bars = 0
        self.seed_submitted = False
        self.target_submitted = False
        self.evidence: dict = {}

    def on_start(self) -> None:
        self.subscribe_bars(self.bar_type)

    def on_bar(self, bar: Bar) -> None:
        self.bars += 1
        instrument = self.cache.instrument(self.instrument_id)
        assert instrument is not None

        if not self.seed_submitted and self.bars == 1:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=Quantity(self.seed_qty, precision=instrument.size_precision),
            )
            self.submit_order(order)
            self.seed_submitted = True
            self.evidence["seed_client_order_id"] = str(order.client_order_id)
            return

        if self.seed_submitted and not self.target_submitted and self.bars >= 3:
            current = Decimal(str(self.portfolio.net_position(self.instrument_id)))
            intent = TargetPositionIntent(
                instrument_id=self.instrument_id,
                target=self.target_qty,
                reason="B6 spike: raise target from seed",
                tsd_command_id=self.tsd_command_id,
            )
            plan = compute_delta(current, intent)
            self.evidence["current_before_target"] = str(current)
            self.evidence["target"] = str(intent.target)
            self.evidence["derived_side"] = plan.side.name
            self.evidence["derived_qty"] = str(plan.quantity)

            order = plan_to_market_order(
                self, plan, precision=instrument.size_precision,
            )
            if order is not None:
                self.submit_order(order)
                self.evidence["target_client_order_id"] = str(order.client_order_id)
            self.target_submitted = True

        if self.target_submitted and self.bars >= 5:
            final = Decimal(str(self.portfolio.net_position(self.instrument_id)))
            self.evidence["final_position"] = str(final)
            self.evidence["realized_pnl"] = str(self.portfolio.realized_pnl(self.instrument_id))
            self.evidence["unrealized_pnl"] = str(self.portfolio.unrealized_pnl(self.instrument_id))


def _make_bars(instrument, bar_type: BarType, n: int = 12) -> list[Bar]:
    bars: list[Bar] = []
    # ~$50k BTC flat tape — enough for fills without wild PnL noise
    px = Decimal("50000.00")
    for i in range(n):
        ts = 1_700_000_000_000_000_000 + i * 60_000_000_000
        price = Price(px, precision=instrument.price_precision)
        bars.append(
            Bar(
                bar_type=bar_type,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=Quantity(Decimal("10"), precision=instrument.size_precision),
                ts_event=ts,
                ts_init=ts,
            ),
        )
    return bars


def run() -> dict:
    venue = Venue("BINANCE")
    instrument = TestInstrumentProvider.btcusdt_binance()
    # Provider already tags BINANCE; ensure venue matches for cash account
    assert instrument.id.venue == venue

    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=TraderId("TSD-SPIKE-001"),
            logging=LoggingConfig(log_level="ERROR"),
        ),
    )
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=None,
        starting_balances=[Money(1_000_000, USDT)],
    )
    engine.add_instrument(instrument)

    bar_type = BarType(
        instrument.id,
        BarSpecification(1, BarAggregation.MINUTE, PriceType.LAST),
        AggregationSource.EXTERNAL,
    )
    strategy = TargetPositionDemoStrategy(
        TargetDemoConfig(
            instrument_id=instrument.id,
            bar_type=bar_type,
        ),
    )
    engine.add_strategy(strategy)
    engine.add_data(_make_bars(instrument, bar_type))
    engine.run()

    evidence = dict(strategy.evidence)
    evidence["nautilus_version"] = __import__("nautilus_trader").__version__
    evidence["instrument"] = str(instrument.id)
    engine.dispose()
    return evidence


def main() -> None:
    evidence = run()
    print("=== B6 TargetPositionIntent evidence ===")
    for k, v in evidence.items():
        print(f"{k}: {v}")

    assert evidence["derived_side"] == "BUY", evidence
    assert Decimal(evidence["derived_qty"]) == Decimal("0.02"), evidence
    assert Decimal(evidence["current_before_target"]) == Decimal("0.18"), evidence
    assert Decimal(evidence["final_position"]) == Decimal("0.20"), evidence
    print("PASS: 0.18 → target 0.20 → derived BUY 0.02 → final 0.20")


if __name__ == "__main__":
    main()
