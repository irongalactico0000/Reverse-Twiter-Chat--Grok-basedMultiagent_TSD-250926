from core.types.exchange import Exchange
from osm.managers.binance import BinanceOrderManager
from osm.managers.bybit import BybitOrderManager
from osm.managers.coinbase import CoinbaseOrderManager


class OrderServiceManager:
    def __init__(self, config: dict):
        self.config = config

    def get(self, exchange: Exchange):
        match exchange:
            case Exchange.BINANCE:
                return BinanceOrderManager(*self.config["binance"])
            case Exchange.BYBIT:
                return BybitOrderManager(*self.config["bybit"])
            case Exchange.COINBASE:
                return CoinbaseOrderManager(*self.config["coinbase"])
            case Exchange.ALPACA:
                from osm.managers.alpaca import AlpacaOrderManager
                cfg = self.config.get("alpaca", {})
                return AlpacaOrderManager(cfg["api_key"], cfg["secret_key"], cfg.get("paper", True))
            case Exchange.IB:
                from osm.managers.interactive_brokers import IBOrderManager
                cfg = self.config.get("ib", {})
                return IBOrderManager(cfg.get("host", "127.0.0.1"), cfg.get("port", 7497), cfg.get("client_id", 1))
            case Exchange.CTRADER:
                from osm.managers.ctrader import CTraderOrderManager
                cfg = self.config.get("ctrader", {})
                return CTraderOrderManager(**cfg)
            case _:
                raise ValueError(f"Unsupported exchange: {exchange}")