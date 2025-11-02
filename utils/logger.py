import structlog
import logging
import sys
from config import SYSTEM_CONFIG

def setup_logger():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, SYSTEM_CONFIG["LOG_LEVEL"]),
    )
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, SYSTEM_CONFIG["LOG_LEVEL"])
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    return structlog.get_logger(name)
