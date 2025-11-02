import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_CONFIG = {
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    "DATA_PATH": os.getenv("DATA_PATH", "./data"),
    "MODELS_PATH": os.getenv("MODELS_PATH", "./models"),
    
    "MAX_CONCURRENT_TASKS": 50,
    "TASK_TIMEOUT": 30,
    "MEMORY_LIMIT_MB": 512,
    
    "HEALTH_CHECK_INTERVAL": 30,
    "PERFORMANCE_METRICS_INTERVAL": 60,
    "ALERT_ENABLED": True,
}
