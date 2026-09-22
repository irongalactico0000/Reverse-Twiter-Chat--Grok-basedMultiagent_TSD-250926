"""Singleton managing all broker connections for the lifetime of the FastAPI app."""
import asyncio
import os
from dotenv import load_dotenv

from .broker_connection import BrokerConnection, BrokerInfo, ConnectionStatus
from .brokers.alpaca import AlpacaBrokerConnection
from .brokers.interactive_brokers import IBBrokerConnection
from .brokers.ctrader import CTraderBrokerConnection

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _build_default_brokers() -> dict[str, BrokerConnection]:
    brokers: dict[str, BrokerConnection] = {}

    # Alpaca — always present if keys exist
    alpaca_key = _env("ALPACA_API_KEY")
    alpaca_secret = _env("ALPACA_SECRET_KEY")
    if alpaca_key and alpaca_secret:
        paper = _env("ALPACA_PAPER", "true").lower() != "false"
        brokers["alpaca"] = AlpacaBrokerConnection(alpaca_key, alpaca_secret, paper=paper)

    # Interactive Brokers — always present (connects to TWS/Gateway)
    ib_host = _env("IB_HOST", "127.0.0.1")
    ib_port = int(_env("IB_PORT", "7497"))
    ib_paper = _env("IB_PAPER", "true").lower() != "false"
    brokers["ib"] = IBBrokerConnection(host=ib_host, port=ib_port, paper=ib_paper)

    # cTrader — present if credentials exist
    ct_client_id = _env("CTRADER_CLIENT_ID")
    ct_client_secret = _env("CTRADER_CLIENT_SECRET")
    ct_token = _env("CTRADER_ACCESS_TOKEN")
    ct_account = _env("CTRADER_ACCOUNT_ID")
    if ct_client_id and ct_client_secret and ct_token and ct_account:
        ct_demo = _env("CTRADER_DEMO", "true").lower() != "false"
        brokers["ctrader"] = CTraderBrokerConnection(
            client_id=ct_client_id,
            client_secret=ct_client_secret,
            access_token=ct_token,
            account_id=int(ct_account),
            demo=ct_demo,
        )

    return brokers


class BrokerPool:
    def __init__(self):
        self._brokers: dict[str, BrokerConnection] = _build_default_brokers()

    def list_brokers(self) -> list[BrokerInfo]:
        return [b.get_info() for b in self._brokers.values()]

    def get(self, broker_id: str) -> BrokerConnection | None:
        return self._brokers.get(broker_id)

    async def connect(self, broker_id: str) -> BrokerInfo:
        broker = self._brokers.get(broker_id)
        if not broker:
            raise ValueError(f"Unknown broker: {broker_id}")
        await broker.connect()
        return broker.get_info()

    async def disconnect(self, broker_id: str) -> BrokerInfo:
        broker = self._brokers.get(broker_id)
        if not broker:
            raise ValueError(f"Unknown broker: {broker_id}")
        await broker.disconnect()
        return broker.get_info()

    async def connect_all(self) -> None:
        """Try connecting all brokers concurrently on startup — failures are swallowed."""
        results = await asyncio.gather(
            *[b.connect() for b in self._brokers.values()],
            return_exceptions=True,
        )
        for broker_id, result in zip(self._brokers, results):
            if isinstance(result, Exception):
                print(f"[BrokerPool] {broker_id} connect failed: {result}")

    async def get_all_positions(self) -> list[dict]:
        connected = [b for b in self._brokers.values() if b.status == ConnectionStatus.CONNECTED]
        results = await asyncio.gather(*[b.get_positions() for b in connected], return_exceptions=True)
        positions = []
        for res in results:
            if isinstance(res, list):
                positions.extend(res)
        return positions

    async def get_all_orders(self) -> list[dict]:
        connected = [b for b in self._brokers.values() if b.status == ConnectionStatus.CONNECTED]
        results = await asyncio.gather(*[b.get_open_orders() for b in connected], return_exceptions=True)
        orders = []
        for res in results:
            if isinstance(res, list):
                orders.extend(res)
        return orders


# App-level singleton — created once in lifespan
_pool: BrokerPool | None = None


def get_pool() -> BrokerPool:
    global _pool
    if _pool is None:
        _pool = BrokerPool()
    return _pool
