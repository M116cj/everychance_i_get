import os
from dotenv import load_dotenv

load_dotenv()

TRADING_CONFIG = {
    "TRADING_ENABLED": os.getenv("TRADING_ENABLED", "False").lower() == "true",
    "PAPER_TRADING": os.getenv("PAPER_TRADING", "True").lower() == "true",
    
    "TRADING_CYCLE_INTERVAL": 60,
    "POSITION_MONITOR_INTERVAL": 2,
    "MARKET_SCAN_INTERVAL": 10,
    
    "MAX_CONCURRENT_POSITIONS": int(os.getenv("MAX_CONCURRENT_POSITIONS", "5")),
    "MIN_POSITION_SIZE": 10.0,
    "MAX_POSITION_SIZE": 1000.0,
    "MAX_PORTFOLIO_EXPOSURE": 0.8,
    
    "ORDER_TIMEOUT": 30,
    "ORDER_RETRY_ATTEMPTS": 3,
    "SLIPPAGE_TOLERANCE": 0.001,
}
