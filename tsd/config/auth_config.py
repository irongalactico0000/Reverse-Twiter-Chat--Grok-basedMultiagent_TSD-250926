import os
from dotenv import load_dotenv

from core.types.exchange import Exchange

# Load .env file
load_dotenv()

# === Basic Settings ===
def require_env(var_name: str) -> str:
    val = os.getenv(var_name)
    if not val:
        raise EnvironmentError(f"Missing environment variable: {var_name}")
    return val

# Constants
TIMEOUT = float(os.getenv("OSM_HTTP_TIMEOUT", "1.0"))
ENV = os.getenv("OSM_ENV", "local")

# === Credential Getter ===
def get_exchange_credentials(exchange: Exchange) -> dict:
    match exchange:
        case Exchange.BINANCE:
            return {
                "api_key": require_env("BINANCE_API_KEY"),
                "secret_key": require_env("BINANCE_SECRET"),
            }
        case Exchange.COINBASE:
            return {
                "api_key": require_env("COINBASE_API_KEY"),
                "secret_key": require_env("COINBASE_SECRET_KEY"),
                "passphrase": os.getenv("COINBASE_PASSPHRASE", ""),
            }
        case Exchange.BYBIT:
            return {
                "api_key": require_env("BYBIT_API_KEY"),
                "secret_key": require_env("BYBIT_SECRET_KEY"),
            }
        case Exchange.OKX:
            return {
                "api_key": require_env("OKX_API_KEY"),
                "secret_key": require_env("OKX_SECRET_KEY"),
            }
        case Exchange.ALPACA:
            return {
                "api_key": require_env("ALPACA_API_KEY"),
                "secret_key": require_env("ALPACA_SECRET_KEY"),
                "paper": os.getenv("ALPACA_PAPER", "true").lower() != "false",
            }
        case Exchange.IB:
            return {
                "host": os.getenv("IB_HOST", "127.0.0.1"),
                "port": int(os.getenv("IB_PORT", "7497")),
                "client_id": int(os.getenv("IB_CLIENT_ID", "1")),
                "paper": os.getenv("IB_PAPER", "true").lower() != "false",
            }
        case Exchange.CTRADER:
            return {
                "client_id": require_env("CTRADER_CLIENT_ID"),
                "client_secret": require_env("CTRADER_CLIENT_SECRET"),
                "access_token": require_env("CTRADER_ACCESS_TOKEN"),
                "account_id": int(require_env("CTRADER_ACCOUNT_ID")),
                "demo": os.getenv("CTRADER_DEMO", "true").lower() != "false",
            }
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")

# === .env.example Generator ===
def generate_env_example(path=".env.example"):
    lines = [
        "# === General Settings ===",
        "OSM_HTTP_TIMEOUT=1.0",
        "OSM_ENV=local",
        "",
        "# === Binance ===",
        "BINANCE_API_KEY=your_binance_api_key",
        "BINANCE_SECRET=your_binance_secret",
        "",
        "# === Coinbase ===",
        "COINBASE_API_KEY=your_coinbase_api_key",
        "COINBASE_SECRET_KEY=your_coinbase_secret",
        "COINBASE_PASSPHRASE=your_coinbase_passphrase",
        "",
        "# === Bybit ===",
        "BYBIT_API_KEY=your_bybit_api_key",
        "BYBIT_SECRET_KEY=your_bybit_secret",
        "",
        "# === OKX ===",
        "OKX_API_KEY=your_okx_api_key",
        "OKX_SECRET_KEY=your_okx_secret",
        "",
        "# === Alpaca ===",
        "ALPACA_API_KEY=your_alpaca_api_key",
        "ALPACA_SECRET_KEY=your_alpaca_secret_key",
        "ALPACA_PAPER=true",
        "",
        "# === Interactive Brokers ===",
        "IB_HOST=127.0.0.1",
        "IB_PORT=7497",
        "IB_CLIENT_ID=1",
        "IB_PAPER=true",
        "",
        "# === cTrader ===",
        "CTRADER_CLIENT_ID=your_ctrader_client_id",
        "CTRADER_CLIENT_SECRET=your_ctrader_client_secret",
        "CTRADER_ACCESS_TOKEN=your_ctrader_access_token",
        "CTRADER_ACCOUNT_ID=your_ctrader_account_id",
        "CTRADER_DEMO=true",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"[CONFIG] Generated {path}")
