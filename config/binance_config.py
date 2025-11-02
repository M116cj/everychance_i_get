import os
from dotenv import load_dotenv

load_dotenv()

BINANCE_CONFIG = {
    "API_KEY": os.getenv("BINANCE_API_KEY", ""),
    "API_SECRET": os.getenv("BINANCE_API_SECRET", ""),
    "TESTNET": os.getenv("BINANCE_TESTNET", "True").lower() == "true",
    
    "REST_BASE_URL": "https://api.binance.com",
    "TESTNET_BASE_URL": "https://testnet.binance.vision",
    "RATE_LIMIT_REQUESTS": 1200,
    "RATE_LIMIT_PERIOD": 60,
    
    "WS_BASE_URL": "wss://stream.binance.com:9443/ws",
    "WS_TESTNET_URL": "wss://testnet.binance.vision/ws",
    "WS_TIMEOUT": 10,
    "WS_RECONNECT_DELAY": 5,
    "WS_MAX_RECONNECT_ATTEMPTS": 5,
    
    "SYMBOLS": [
        "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
        "BNBUSDT", "XRPUSDT", "LTCUSDT", "BCHUSDT", "EOSUSDT"
    ],
    
    "STREAMS": [
        "kline_1m", "kline_5m", "kline_15m", "kline_1h",
        "trade", "depth"
    ],
    
    "ENDPOINTS": {
        "exchange_info": "/api/v3/exchangeInfo",
        "klines": "/api/v3/klines",
        "ticker_24hr": "/api/v3/ticker/24hr",
        "account_info": "/api/v3/account",
        "create_order": "/api/v3/order",
        "query_order": "/api/v3/order",
        "cancel_order": "/api/v3/order",
        "open_orders": "/api/v3/openOrders",
        "all_orders": "/api/v3/allOrders",
    }
}
