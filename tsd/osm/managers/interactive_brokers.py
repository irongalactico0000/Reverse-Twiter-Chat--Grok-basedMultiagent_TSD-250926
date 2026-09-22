"""Interactive Brokers order manager for tsd/osm — via ib_async."""
from core.types.trade import ExternalOrder
from osm.core.base import BaseOrderManager


class IBOrderManager(BaseOrderManager):
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self._ib = None

    async def _ensure_connected(self):
        if self._ib is None or not self._ib.isConnected():
            from ib_async import IB
            self._ib = IB()
            await self._ib.connectAsync(self.host, self.port, clientId=self.client_id)

    async def send_order(self, order: ExternalOrder) -> dict:
        from ib_async import Stock, MarketOrder, LimitOrder

        await self._ensure_connected()
        contract = Stock(order.symbol, "SMART", "USD")
        await self._ib.qualifyContractsAsync(contract)

        action = "BUY" if order.side == "BUY" else "SELL"
        if order.order_type == "MARKET":
            ib_order = MarketOrder(action, abs(order.qty))
        else:
            ib_order = LimitOrder(action, abs(order.qty), order.price)

        trade = self._ib.placeOrder(contract, ib_order)
        return {
            "exchange": "IB",
            "client_order_id": order.client_order_id,
            "order_id": str(trade.order.orderId),
            "status": str(trade.orderStatus.status),
        }
