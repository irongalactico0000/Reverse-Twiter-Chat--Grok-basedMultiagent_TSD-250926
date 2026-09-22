"""Alpaca order manager for tsd/osm — thin wrapper over alpaca-py."""
import asyncio
from functools import partial

from core.types.trade import ExternalOrder
from osm.core.base import BaseOrderManager


class AlpacaOrderManager(BaseOrderManager):
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self._client = None

    def _get_client(self):
        if self._client is None:
            from alpaca.trading.client import TradingClient
            self._client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.paper,
            )
        return self._client

    async def send_order(self, order: ExternalOrder) -> dict:
        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        client = self._get_client()
        side = OrderSide.BUY if order.side == "BUY" else OrderSide.SELL

        if order.order_type == "MARKET":
            req = MarketOrderRequest(
                symbol=order.symbol,
                qty=abs(order.qty),
                side=side,
                time_in_force=TimeInForce.DAY,
            )
        else:
            req = LimitOrderRequest(
                symbol=order.symbol,
                qty=abs(order.qty),
                side=side,
                limit_price=order.price,
                time_in_force=TimeInForce.DAY,
            )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, partial(client.submit_order, req))
        return {
            "exchange": "ALPACA",
            "client_order_id": order.client_order_id,
            "order_id": str(result.id),
            "status": str(result.status),
        }
