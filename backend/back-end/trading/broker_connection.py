from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class ConnectionStatus(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


@dataclass
class BrokerInfo:
    id: str
    name: str
    status: ConnectionStatus
    supports_orders: bool
    is_paper: bool
    status_detail: str = ""
    error: str | None = None


@dataclass
class OrderRequest:
    symbol: str
    side: str           # BUY | SELL
    order_type: str     # MARKET | LIMIT
    quantity: float
    price: float | None = None
    time_in_force: str = "DAY"
    client_order_id: str | None = None


class BrokerConnection(ABC):
    """Abstract base for all stateful broker connections (Alpaca, IB, cTrader)."""

    id: str
    name: str
    is_paper: bool

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @property
    @abstractmethod
    def status(self) -> ConnectionStatus: ...

    @property
    @abstractmethod
    def status_detail(self) -> str: ...

    @property
    @abstractmethod
    def supports_orders(self) -> bool: ...

    @abstractmethod
    async def send_order(self, order: OrderRequest) -> dict: ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> dict: ...

    @abstractmethod
    async def get_positions(self) -> list[dict]: ...

    @abstractmethod
    async def get_open_orders(self) -> list[dict]: ...

    def get_info(self) -> BrokerInfo:
        return BrokerInfo(
            id=self.id,
            name=self.name,
            status=self.status,
            supports_orders=self.supports_orders,
            is_paper=self.is_paper,
            status_detail=self.status_detail,
        )
