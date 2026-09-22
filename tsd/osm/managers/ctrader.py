"""cTrader order manager for tsd/osm — stub pending full protobuf integration."""
from core.types.trade import ExternalOrder
from osm.core.base import BaseOrderManager


class CTraderOrderManager(BaseOrderManager):
    def __init__(self, client_id: str, client_secret: str, access_token: str, account_id: int, demo: bool = True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.account_id = account_id
        self.demo = demo

    async def send_order(self, order: ExternalOrder) -> dict:
        # Full implementation requires protobuf encoding of ProtoOANewOrderReq.
        # See: https://github.com/spotware/openapi-proto-messages
        raise NotImplementedError(
            "cTrader order submission requires full Open API protobuf integration. "
            "Use the backend/back-end/trading/brokers/ctrader.py connection for status."
        )
