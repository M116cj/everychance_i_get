import os
from dotenv import load_dotenv

load_dotenv()

RISK_CONFIG = {
    "MAX_LEVERAGE": int(os.getenv("MAX_LEVERAGE", "125")),
    "BOOTSTRAP_MAX_LEVERAGE": 3.0,
    "LEVERAGE_MULTIPLIER": 3.75,
    
    "DAILY_LOSS_LIMIT": float(os.getenv("DAILY_LOSS_LIMIT", "0.05")),
    "MAX_DRAWDOWN": float(os.getenv("MAX_DRAWDOWN", "0.10")),
    "SINGLE_TRADE_RISK": 0.02,
    
    "STOP_LOSS_ENABLED": True,
    "TRAILING_STOP_ENABLED": True,
    "HARD_STOP_LOSS": 0.10,
    
    "CIRCUIT_BREAKER_ENABLED": True,
    "MAX_CONSECUTIVE_LOSSES": 5,
    "COOLDOWN_PERIOD": 300,
}
