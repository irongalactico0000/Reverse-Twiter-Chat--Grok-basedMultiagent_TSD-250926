from enum import StrEnum


class Exchange(StrEnum):
    # Crypto
    COINBASE = "COINBASE"
    BYBIT = "BYBIT"
    BINANCE = "BINANCE"
    OKX = "OKX"
    UPBIT = "UPBIT"
    BITGET = "BITGET"
    MEXC = "MEXC"
    CDC = "CDC"          # Crypto.com Exchange
    HTX = "HTX"
    GATEIO = "GATEIO"
    # Traditional / multi-asset (data + execution)
    IB = "IB"            # Interactive Brokers (TWS / IB Gateway)
    ALPACA = "ALPACA"    # Alpaca Markets
    CTRADER = "CTRADER"  # cTrader Open API


if __name__ == "__main__":
    coinbase = Exchange.COINBASE
    print(coinbase)
