"""Minimal Nautilus 1.231.0 backtest: apply TargetPositionIntent via derived delta.

Uses synthetic BTCUSDT 1-minute bars on BINANCE venue. Not live. Not production.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, LoggingConfig, StrategyConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import (
    AccountType,
    AggregationSource,
    BarAggregation,
    OmsType,
    OrderSide,
    PriceType,
)
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from target_position import TargetPositionIntent, TargetType, plan_from_intent


class TargetFollowerConfig(StrategyConfig, frozen=True):
    instrument_id: str
    bar_type: str
    target_quantity: str
    seed_quantity: str = "0.18"


class TargetFollower(Strategy):
    """First bar: seed to seed_quantity. Second bar: retarget to target_quantity."""

    def __init__(self, config: TargetFollowerConfig) -> None:
        super().__init__(config)
        self._bars = 0
        self._seed_done = False
        self._target_done = False

    def on_start(self) -> None:
        self.subscribe_bars(BarType.from_str(self.config.bar_type))

    def on_bar(self, bar: Bar) -> None:
        self._bars += 1
        instrument = self.cache.instrument(bar.bar_type.instrument_id)
        if instrument is None:
            return

        current = self.portfolio.net_position(bar.bar_type.instrument_id)
        current_qty = Decimal(str(current))

        if not self._seed_done:
            intent = TargetPositionIntent(
                instrument_id=str(bar.bar_type.instrument_id),
                target_type=TargetType.QUANTITY,
                target_value=Decimal(self.config.seed_quantity),
                reason="seed",
            )
            plan = plan_from_intent(intent, current_quantity=current_qty)
            self._submit_plan(instrument, plan)
            self._seed_done = True
            return

        if not self._target_done and self._bars >= 2:
            intent = TargetPositionIntent(
                instrument_id=str(bar.bar_type.instrument_id),
                target_type=TargetType.QUANTITY,
                target_value=Decimal(self.config.target_quantity),
                reason="retarget 0.20",
            )
            plan = plan_from_intent(intent, current_quantity=current_qty)
            self._submit_plan(instrument, plan)
            self._target_done = True

    def _submit_plan(self, instrument, plan) -> None:
        if plan.side == "FLAT" or plan.quantity == 0:
            self.log.info(f"No order: {plan}")
            return
        side = OrderSide.BUY if plan.side == "BUY" else OrderSide.SELL
        order = self.order_factory.market(
            instrument_id=instrument.id,
            order_side=side,
            quantity=instrument.make_qty(plan.quantity),
        )
        self.log.info(
            f"Derived {plan.side} {plan.quantity} "
            f"(current={plan.current_quantity} target={plan.target_quantity})"
        )
        self.submit_order(order)


def build_bars(instrument, n: int = 50, seed: int = 42) -> tuple[BarType, list[Bar]]:
    from nautilus_trader.model.data import BarSpecification

    bar_type = BarType(
        instrument.id,
        BarSpecification(1, BarAggregation.MINUTE, PriceType.LAST),
        AggregationSource.EXTERNAL,
    )
    rng = np.random.default_rng(seed)
    price = 50_000 + np.cumsum(rng.normal(0, 5, n))
    index = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")
    bars: list[Bar] = []
    for ts, px in zip(index, price):
        p = Price(round(float(px), instrument.price_precision), precision=instrument.price_precision)
        bars.append(
            Bar(
                bar_type=bar_type,
                open=p,
                high=p,
                low=p,
                close=p,
                volume=instrument.make_qty(1),
                ts_event=int(ts.value),
                ts_init=int(ts.value),
            )
        )
    return bar_type, bars


def main() -> None:
    instrument = TestInstrumentProvider.btcusdt_binance()
    bar_type, bars = build_bars(instrument)

    engine = BacktestEngine(
        config=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR"),
        ),
    )
    venue = Venue("BINANCE")
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        starting_balances=[Money(1_000_000, USDT)],
    )
    engine.add_instrument(instrument)
    engine.add_data(bars)

    strategy = TargetFollower(
        TargetFollowerConfig(
            instrument_id=str(instrument.id),
            bar_type=str(bar_type),
            target_quantity="0.20",
            seed_quantity="0.18",
        )
    )
    engine.add_strategy(strategy)
    engine.run()

    fills = engine.trader.generate_order_fills_report()
    positions = engine.trader.generate_positions_report()
    net = engine.cache.net_position(instrument.id) if hasattr(engine.cache, "net_position") else None
    # Prefer portfolio via strategy after run
    final_pos = strategy.portfolio.net_position(instrument.id)
    print("fills_rows", 0 if fills is None else len(fills))
    print("positions_rows", 0 if positions is None else len(positions))
    print("final_net_position", final_pos)
    print("target_done", strategy._target_done, "seed_done", strategy._seed_done)

    # Expect roughly 0.20 after seed 0.18 + buy 0.02 (cash venue + fees may affect)
    final_dec = Decimal(str(final_pos))
    assert strategy._seed_done and strategy._target_done
    assert abs(final_dec - Decimal("0.20")) <= Decimal("0.000001"), final_dec
    print("PASS target follower backtest -> net ~= 0.20")
    engine.dispose()


if __name__ == "__main__":
    main()
