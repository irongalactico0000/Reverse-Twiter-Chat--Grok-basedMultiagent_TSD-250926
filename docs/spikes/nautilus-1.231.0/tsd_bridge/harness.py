"""Shared SIM backtest harness for B6–B9 spike proofs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

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
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

from tsd_bridge import TargetPositionIntent, compute_delta, plan_to_market_order


def make_bars(instrument, bar_type: BarType, n: int = 20, px: str = "50000.00") -> list[Bar]:
    bars: list[Bar] = []
    price_d = Decimal(px)
    for i in range(n):
        ts = 1_700_000_000_000_000_000 + i * 60_000_000_000
        price = Price(price_d, precision=instrument.price_precision)
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


@dataclass
class ScenarioResult:
    evidence: dict
    orders_submitted: list[str]
    final_position: Decimal


class ScenarioConfig(StrategyConfig, frozen=True):
    instrument_id: object
    bar_type: BarType
    scenario: str = "b6"
    seed_quantity: str = "0.18"
    target_quantity: str = "0.20"
    second_target: str = ""
    tsd_command_id: str = "tsd-cmd-001"
    max_order_qty: str = ""  # if set, strategy refuses plans above this (TSD risk gate)


class ScenarioStrategy(Strategy):
    def __init__(self, config: ScenarioConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.scenario = config.scenario
        self.seed_qty = Decimal(config.seed_quantity)
        self.target_qty = Decimal(config.target_quantity)
        self.second_target = Decimal(config.second_target) if config.second_target else None
        self.tsd_command_id = config.tsd_command_id
        self.max_order_qty = Decimal(config.max_order_qty) if config.max_order_qty else None
        self.bars = 0
        self.seed_done = False
        self.phase = 0
        self.evidence: dict = {"plans": [], "rejects": [], "cancels": []}
        self.orders_submitted: list[str] = []
        self._seen_commands: set[str] = set()

    def on_start(self) -> None:
        self.subscribe_bars(self.bar_type)

    def _net(self) -> Decimal:
        return Decimal(str(self.portfolio.net_position(self.instrument_id)))

    def _submit_plan(self, intent: TargetPositionIntent) -> None:
        # B9-style idempotency: same TSD command id never submits twice from this strategy.
        if intent.tsd_command_id and intent.tsd_command_id in self._seen_commands:
            self.evidence["rejects"].append(
                {"reason": "duplicate_tsd_command_id", "id": intent.tsd_command_id},
            )
            return

        instrument = self.cache.instrument(self.instrument_id)
        current = self._net()
        plan = compute_delta(current, intent)
        self.evidence["plans"].append(
            {
                "current": str(current),
                "target": str(intent.target),
                "side": plan.side.name,
                "qty": str(plan.quantity),
                "cmd": intent.tsd_command_id,
            },
        )

        if plan.is_noop:
            return

        if self.max_order_qty is not None and plan.quantity > self.max_order_qty:
            self.evidence["rejects"].append(
                {
                    "reason": "risk_max_order_qty",
                    "qty": str(plan.quantity),
                    "max": str(self.max_order_qty),
                },
            )
            return

        order = plan_to_market_order(self, plan, precision=instrument.size_precision)
        if order is None:
            return
        self.submit_order(order)
        self.orders_submitted.append(str(order.client_order_id))
        if intent.tsd_command_id:
            self._seen_commands.add(intent.tsd_command_id)

    def on_bar(self, bar: Bar) -> None:
        self.bars += 1
        instrument = self.cache.instrument(self.instrument_id)
        assert instrument is not None

        if not self.seed_done and self.bars == 1:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=Quantity(self.seed_qty, precision=instrument.size_precision),
            )
            self.submit_order(order)
            self.orders_submitted.append(str(order.client_order_id))
            self.seed_done = True
            return

        if self.scenario == "b6" and self.seed_done and self.phase == 0 and self.bars >= 3:
            self._submit_plan(
                TargetPositionIntent(
                    instrument_id=self.instrument_id,
                    target=self.target_qty,
                    tsd_command_id=self.tsd_command_id,
                    reason="primary target",
                ),
            )
            self.phase = 1

        elif self.scenario == "duplicate_target" and self.seed_done and self.bars >= 3:
            if self.phase == 0:
                self._submit_plan(
                    TargetPositionIntent(
                        instrument_id=self.instrument_id,
                        target=self.target_qty,
                        tsd_command_id=self.tsd_command_id,
                    ),
                )
                self.phase = 1
            elif self.phase == 1 and self.bars >= 5:
                # Same command id + same target again
                before = len(self.orders_submitted)
                self._submit_plan(
                    TargetPositionIntent(
                        instrument_id=self.instrument_id,
                        target=self.target_qty,
                        tsd_command_id=self.tsd_command_id,
                    ),
                )
                self.evidence["orders_after_duplicate"] = len(self.orders_submitted) - before
                self.phase = 2

        elif self.scenario == "reversal" and self.seed_done and self.bars >= 3:
            if self.phase == 0:
                self._submit_plan(
                    TargetPositionIntent(
                        instrument_id=self.instrument_id,
                        target=self.target_qty,
                        tsd_command_id=f"{self.tsd_command_id}-up",
                    ),
                )
                self.phase = 1
            elif self.phase == 1 and self.bars >= 5 and self.second_target is not None:
                self._submit_plan(
                    TargetPositionIntent(
                        instrument_id=self.instrument_id,
                        target=self.second_target,
                        tsd_command_id=f"{self.tsd_command_id}-down",
                    ),
                )
                self.phase = 2

        elif self.scenario == "risk_reject" and self.seed_done and self.bars >= 3 and self.phase == 0:
            self._submit_plan(
                TargetPositionIntent(
                    instrument_id=self.instrument_id,
                    target=self.target_qty,
                    tsd_command_id=self.tsd_command_id,
                ),
            )
            self.phase = 1

        elif self.scenario == "cancel_limit" and self.seed_done and self.bars >= 3:
            if self.phase == 0:
                # Resting limit far below market; then cancel.
                order = self.order_factory.limit(
                    instrument_id=self.instrument_id,
                    order_side=OrderSide.BUY,
                    quantity=Quantity(Decimal("0.01"), precision=instrument.size_precision),
                    price=Price(Decimal("1000.00"), precision=instrument.price_precision),
                    time_in_force=TimeInForce.GTC,
                    client_order_id=ClientOrderId("tsd-limit-cancel-001"),
                )
                self.submit_order(order)
                self.orders_submitted.append(str(order.client_order_id))
                self.evidence["limit_client_order_id"] = str(order.client_order_id)
                self.phase = 1
            elif self.phase == 1 and self.bars >= 4:
                order = self.cache.order(ClientOrderId("tsd-limit-cancel-001"))
                if order is not None and order.is_open:
                    self.cancel_order(order)
                    self.evidence["cancels"].append(str(order.client_order_id))
                self.phase = 2

        if self.bars >= 18:
            self.evidence["final_position"] = str(self._net())
            self.evidence["order_count"] = len(self.orders_submitted)


def run_scenario(
    scenario: str,
    *,
    seed: str = "0.18",
    target: str = "0.20",
    second_target: str = "",
    tsd_command_id: str = "tsd-cmd-001",
    max_order_qty: str = "",
    trader_id: str = "TSD-SPIKE-001",
    n_bars: int = 20,
) -> ScenarioResult:
    venue = Venue("BINANCE")
    instrument = TestInstrumentProvider.btcusdt_binance()
    assert instrument.id.venue == venue

    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=TraderId(trader_id),
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
    strategy = ScenarioStrategy(
        ScenarioConfig(
            instrument_id=instrument.id,
            bar_type=bar_type,
            scenario=scenario,
            seed_quantity=seed,
            target_quantity=target,
            second_target=second_target,
            tsd_command_id=tsd_command_id,
            max_order_qty=max_order_qty,
        ),
    )
    engine.add_strategy(strategy)
    engine.add_data(make_bars(instrument, bar_type, n=n_bars))
    engine.run()

    evidence = dict(strategy.evidence)
    evidence["scenario"] = scenario
    final = Decimal(evidence.get("final_position", str(strategy._net())))
    engine.dispose()
    return ScenarioResult(
        evidence=evidence,
        orders_submitted=list(strategy.orders_submitted),
        final_position=final,
    )
