import asyncio
from functools import partial

from ..broker_connection import BrokerConnection, BrokerInfo, ConnectionStatus, OrderRequest


class AlpacaBrokerConnection(BrokerConnection):
    """Alpaca broker — REST via alpaca-py. Paper URL used when is_paper=True."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.id = "alpaca"
        self.name = "Alpaca"
        self.api_key = api_key
        self.secret_key = secret_key
        self.is_paper = paper
        self._status = ConnectionStatus.DISCONNECTED
        self._status_detail = ""
        self._client = None

    async def connect(self) -> None:
        self._status = ConnectionStatus.CONNECTING
        self._status_detail = "Checking API key…"
        try:
            from alpaca.trading.client import TradingClient
            loop = asyncio.get_event_loop()
            client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.is_paper,
            )
            account = await loop.run_in_executor(None, client.get_account)
            self._client = client
            mode = "paper" if self.is_paper else "live"
            self._status_detail = f"API key works ({mode} URL) — equity ${float(account.equity):,.2f}"
            self._status = ConnectionStatus.CONNECTED
        except ImportError:
            self._status = ConnectionStatus.ERROR
            self._status_detail = "alpaca-py not installed (pip install alpaca-py)"
        except Exception as exc:
            self._status = ConnectionStatus.ERROR
            self._status_detail = str(exc)

    async def disconnect(self) -> None:
        self._client = None
        self._status = ConnectionStatus.DISCONNECTED
        self._status_detail = ""

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def status_detail(self) -> str:
        return self._status_detail

    @property
    def supports_orders(self) -> bool:
        return True

    async def send_order(self, order: OrderRequest) -> dict:
        if not self._client:
            raise RuntimeError("Alpaca not connected")
        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        side = OrderSide.BUY if order.side.upper() == "BUY" else OrderSide.SELL
        tif_map = {"DAY": TimeInForce.DAY, "GTC": TimeInForce.GTC, "IOC": TimeInForce.IOC}
        tif = tif_map.get(order.time_in_force.upper(), TimeInForce.DAY)

        if order.order_type.upper() == "MARKET":
            req = MarketOrderRequest(symbol=order.symbol, qty=order.quantity, side=side, time_in_force=tif)
        else:
            req = LimitOrderRequest(
                symbol=order.symbol, qty=order.quantity,
                side=side, limit_price=order.price, time_in_force=tif,
            )
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, partial(self._client.submit_order, req))
        return {"exchange": "ALPACA", "order_id": str(result.id), "status": str(result.status)}

    async def cancel_order(self, order_id: str) -> dict:
        if not self._client:
            raise RuntimeError("Alpaca not connected")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, partial(self._client.cancel_order_by_id, order_id))
        return {"cancelled": order_id}

    async def get_positions(self) -> list[dict]:
        if not self._client:
            return []
        loop = asyncio.get_event_loop()
        positions = await loop.run_in_executor(None, self._client.get_all_positions)
        return [
            {
                "broker": "alpaca",
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "side": str(p.side),
            }
            for p in positions
        ]

    async def get_open_orders(self) -> list[dict]:
        if not self._client:
            return []
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        loop = asyncio.get_event_loop()
        req = GetOrdersRequest(status=QueryOrderStatus.OPEN)
        orders = await loop.run_in_executor(None, partial(self._client.get_orders, req))
        return [
            {
                "broker": "alpaca",
                "id": str(o.id),
                "symbol": o.symbol,
                "side": str(o.side),
                "qty": float(o.qty),
                "filled_qty": float(o.filled_qty),
                "order_type": str(o.order_type),
                "status": str(o.status),
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
            }
            for o in orders
        ]
