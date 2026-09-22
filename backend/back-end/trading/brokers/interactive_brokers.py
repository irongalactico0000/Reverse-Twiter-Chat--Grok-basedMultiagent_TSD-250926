from ..broker_connection import BrokerConnection, ConnectionStatus, OrderRequest


class IBBrokerConnection(BrokerConnection):
    """Interactive Brokers via ib_async (connects to TWS or IB Gateway).

    Paper: port 7497 (TWS paper) or 4002 (Gateway paper).
    Live:  port 7496 (TWS live)  or 4001 (Gateway live).
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        paper: bool = True,
    ):
        self.id = "ib"
        self.name = "Interactive Brokers"
        self.host = host
        self.port = port
        self.client_id = client_id
        self.is_paper = paper
        self._status = ConnectionStatus.DISCONNECTED
        self._status_detail = ""
        self._ib = None

    async def connect(self) -> None:
        self._status = ConnectionStatus.CONNECTING
        self._status_detail = f"Connecting to TWS/Gateway at {self.host}:{self.port}…"
        try:
            from ib_async import IB
            ib = IB()
            await ib.connectAsync(self.host, self.port, clientId=self.client_id)
            self._ib = ib
            accounts = ib.managedAccounts()
            acct = accounts[0] if accounts else "unknown"
            mode = "paper" if self.is_paper else "live"
            self._status_detail = f"Talking to TWS / IB Gateway ({mode}) — account {acct}"
            self._status = ConnectionStatus.CONNECTED
        except ImportError:
            self._status = ConnectionStatus.ERROR
            self._status_detail = "ib-async not installed (pip install ib-async)"
        except ConnectionRefusedError:
            self._status = ConnectionStatus.ERROR
            self._status_detail = f"TWS / IB Gateway not running on {self.host}:{self.port}"
        except Exception as exc:
            self._status = ConnectionStatus.ERROR
            self._status_detail = str(exc)

    async def disconnect(self) -> None:
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
        self._ib = None
        self._status = ConnectionStatus.DISCONNECTED
        self._status_detail = ""

    @property
    def status(self) -> ConnectionStatus:
        if self._ib and not self._ib.isConnected() and self._status == ConnectionStatus.CONNECTED:
            self._status = ConnectionStatus.DISCONNECTED
            self._status_detail = "Connection dropped"
        return self._status

    @property
    def status_detail(self) -> str:
        return self._status_detail

    @property
    def supports_orders(self) -> bool:
        return True

    async def send_order(self, order: OrderRequest) -> dict:
        if not self._ib or not self._ib.isConnected():
            raise RuntimeError("IB not connected")
        from ib_async import MarketOrder, LimitOrder, Stock, Forex

        # Resolve contract — default to stock, try forex for pairs like EUR.USD
        if "." in order.symbol or "/" in order.symbol:
            base, term = order.symbol.replace("/", ".").split(".")
            contract = Forex(base + term)
        else:
            contract = Stock(order.symbol, "SMART", "USD")

        await self._ib.qualifyContractsAsync(contract)
        action = "BUY" if order.side.upper() == "BUY" else "SELL"

        if order.order_type.upper() == "MARKET":
            ib_order = MarketOrder(action, order.quantity)
        else:
            ib_order = LimitOrder(action, order.quantity, order.price)

        trade = self._ib.placeOrder(contract, ib_order)
        return {"exchange": "IB", "order_id": str(trade.order.orderId), "status": str(trade.orderStatus.status)}

    async def cancel_order(self, order_id: str) -> dict:
        if not self._ib or not self._ib.isConnected():
            raise RuntimeError("IB not connected")
        open_trades = self._ib.openTrades()
        for trade in open_trades:
            if str(trade.order.orderId) == order_id:
                self._ib.cancelOrder(trade.order)
                return {"cancelled": order_id}
        return {"error": f"Order {order_id} not found in open trades"}

    async def get_positions(self) -> list[dict]:
        if not self._ib or not self._ib.isConnected():
            return []
        positions = self._ib.positions()
        return [
            {
                "broker": "ib",
                "symbol": p.contract.symbol,
                "qty": p.position,
                "avg_entry_price": p.avgCost,
                "market_value": None,
                "unrealized_pl": None,
                "side": "LONG" if p.position > 0 else "SHORT",
            }
            for p in positions
        ]

    async def get_open_orders(self) -> list[dict]:
        if not self._ib or not self._ib.isConnected():
            return []
        trades = self._ib.openTrades()
        return [
            {
                "broker": "ib",
                "id": str(t.order.orderId),
                "symbol": t.contract.symbol,
                "side": t.order.action,
                "qty": t.order.totalQuantity,
                "filled_qty": t.orderStatus.filled,
                "order_type": t.order.orderType,
                "status": t.orderStatus.status,
                "limit_price": t.order.lmtPrice if t.order.lmtPrice != 0 else None,
                "submitted_at": None,
            }
            for t in trades
        ]
