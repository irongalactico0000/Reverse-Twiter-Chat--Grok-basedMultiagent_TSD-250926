import asyncio
import json
import ssl
from ..broker_connection import BrokerConnection, ConnectionStatus, OrderRequest


class CTraderBrokerConnection(BrokerConnection):
    """cTrader Open API broker connection.

    Uses the ctrader-open-api WebSocket endpoint with OAuth2 tokens.
    Requires: CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_ACCESS_TOKEN,
              CTRADER_ACCOUNT_ID in environment.
    """

    LIVE_HOST = "live.ctraderapi.com"
    DEMO_HOST = "demo.ctraderapi.com"
    PORT = 5035

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        account_id: int,
        demo: bool = True,
    ):
        self.id = "ctrader"
        self.name = "cTrader"
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.account_id = account_id
        self.is_paper = demo
        self._status = ConnectionStatus.DISCONNECTED
        self._status_detail = ""
        self._reader = None
        self._writer = None
        self._authorized = False

    async def connect(self) -> None:
        self._status = ConnectionStatus.CONNECTING
        host = self.DEMO_HOST if self.is_paper else self.LIVE_HOST
        self._status_detail = f"Connecting to {host}:{self.PORT}…"
        try:
            # cTrader Open API uses TLS over TCP with protobuf messages.
            # We use ctrader-open-api library's Twisted reactor in a thread,
            # or fall back to asyncio raw TLS socket approach.
            try:
                await self._connect_via_library()
            except ImportError:
                await self._connect_raw_tls(host)
        except Exception as exc:
            self._status = ConnectionStatus.ERROR
            self._status_detail = str(exc)

    async def _connect_via_library(self) -> None:
        """Use ctrader-open-api if installed."""
        from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
        # ctrader-open-api is Twisted-based; run in executor thread
        loop = asyncio.get_event_loop()
        host = EndPoints.PROTOBUF_DEMO_HOST if self.is_paper else EndPoints.PROTOBUF_LIVE_HOST

        def _blocking_connect():
            # Minimal handshake — full impl requires Twisted reactor
            raise NotImplementedError("Twisted reactor integration pending; use raw TLS path")

        await loop.run_in_executor(None, _blocking_connect)

    async def _connect_raw_tls(self, host: str) -> None:
        """Direct asyncio TLS connection with minimal Open API handshake."""
        ctx = ssl.create_default_context()
        self._reader, self._writer = await asyncio.open_connection(host, self.PORT, ssl=ctx)
        # Send APPLICATION_AUTH_REQ
        auth_msg = json.dumps({
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "payloadType": 2100,  # ProtoOAApplicationAuthReq
        }).encode()
        self._writer.write(len(auth_msg).to_bytes(4, "big") + auth_msg)
        await self._writer.drain()

        # Read response
        raw_len = await self._reader.read(4)
        if len(raw_len) < 4:
            raise ConnectionError("No response from cTrader API")
        resp_len = int.from_bytes(raw_len, "big")
        resp_data = await self._reader.read(resp_len)
        resp = json.loads(resp_data)

        if resp.get("errorCode"):
            raise ConnectionError(f"cTrader auth error: {resp['errorCode']}")

        # Account auth
        acct_msg = json.dumps({
            "accessToken": self.access_token,
            "ctidTraderAccountId": self.account_id,
            "payloadType": 2102,  # ProtoOAAccountAuthReq
        }).encode()
        self._writer.write(len(acct_msg).to_bytes(4, "big") + acct_msg)
        await self._writer.drain()

        raw_len = await self._reader.read(4)
        resp_data = await self._reader.read(int.from_bytes(raw_len, "big"))
        resp = json.loads(resp_data)

        if resp.get("errorCode"):
            raise ConnectionError(f"cTrader account auth error: {resp['errorCode']}")

        self._authorized = True
        mode = "demo" if self.is_paper else "live"
        self._status_detail = f"Token / account ok ({mode}) — account {self.account_id}"
        self._status = ConnectionStatus.CONNECTED

    async def disconnect(self) -> None:
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._writer = None
        self._reader = None
        self._authorized = False
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
        if not self._authorized:
            raise RuntimeError("cTrader not authenticated")
        # Full protobuf order encoding would go here (ProtoOANewOrderReq, payloadType 2106)
        raise NotImplementedError("cTrader order submission requires full protobuf integration")

    async def cancel_order(self, order_id: str) -> dict:
        raise NotImplementedError("cTrader cancel requires full protobuf integration")

    async def get_positions(self) -> list[dict]:
        # ProtoOAReconcileReq (payloadType 2124) returns open positions
        return []

    async def get_open_orders(self) -> list[dict]:
        return []
