import time
from typing import Callable, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"
        
    async def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("circuit_breaker_half_open", recovery_attempt=True)
            else:
                raise Exception("Circuit breaker is OPEN")
                
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("circuit_breaker_closed", recovered=True)
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error("circuit_breaker_opened", 
                           failure_count=self.failure_count,
                           error=str(e))
                
            raise e
    
    def reset(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0
