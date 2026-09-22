from pydantic import BaseModel
from typing import Any


class BrokerStatusResponse(BaseModel):
    id: str
    name: str
    status: str
    supports_orders: bool
    is_paper: bool
    status_detail: str
    error: str | None = None


class OrderRequestBody(BaseModel):
    broker_id: str
    symbol: str
    side: str           # BUY | SELL
    order_type: str     # MARKET | LIMIT
    quantity: float
    price: float | None = None
    time_in_force: str = "DAY"


class OrderResponse(BaseModel):
    broker_id: str
    result: dict[str, Any]


class CancelOrderBody(BaseModel):
    broker_id: str


class PositionItem(BaseModel):
    broker: str
    symbol: str
    qty: float
    avg_entry_price: float | None = None
    market_value: float | None = None
    unrealized_pl: float | None = None
    side: str | None = None


class OrderItem(BaseModel):
    broker: str
    id: str
    symbol: str
    side: str
    qty: float
    filled_qty: float | None = None
    order_type: str | None = None
    status: str | None = None
    limit_price: float | None = None
    submitted_at: str | None = None
