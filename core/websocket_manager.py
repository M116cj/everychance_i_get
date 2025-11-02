import asyncio
import json
import time
from collections import deque
from typing import Dict, List, Callable, Any, Optional
import websockets
from websockets.exceptions import ConnectionClosed

from config import BINANCE_CONFIG, WEBSOCKET_CONFIG
from utils.logger import get_logger
from utils.circuit_breaker import CircuitBreaker

logger = get_logger(__name__)

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.buffers: Dict[str, deque] = {}
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        self.running = False
        self.latency_stats: Dict[str, float] = {}
        
    async def connect(self, symbols: List[str]):
        self.running = True
        
        base_url = (BINANCE_CONFIG["WS_TESTNET_URL"] 
                   if BINANCE_CONFIG["TESTNET"] 
                   else BINANCE_CONFIG["WS_BASE_URL"])
        
        for symbol in symbols:
            stream_name = f"{symbol.lower()}@kline_1m/{symbol.lower()}@trade"
            url = f"{base_url.replace('/ws', '/stream')}?streams={stream_name}"
            
            asyncio.create_task(self._connect_stream(symbol, url))
            logger.info("websocket_connecting", symbol=symbol, url=url)
        
        logger.info("websocket_manager_started", symbols=symbols)
    
    async def _connect_stream(self, symbol: str, url: str):
        reconnect_attempt = 0
        
        while self.running:
            try:
                async with websockets.connect(
                    url,
                    ping_interval=WEBSOCKET_CONFIG["HEARTBEAT_INTERVAL"],
                    ping_timeout=10
                ) as websocket:
                    self.connections[symbol] = websocket
                    reconnect_attempt = 0
                    logger.info("websocket_connected", symbol=symbol)
                    
                    await self._handle_messages(symbol, websocket)
                    
            except ConnectionClosed as e:
                logger.warning("websocket_connection_closed", 
                             symbol=symbol, 
                             error=str(e))
                await self._handle_reconnect(symbol, reconnect_attempt)
                reconnect_attempt += 1
                
            except Exception as e:
                logger.error("websocket_error", 
                           symbol=symbol, 
                           error=str(e))
                await self._handle_reconnect(symbol, reconnect_attempt)
                reconnect_attempt += 1
    
    async def _handle_messages(self, symbol: str, websocket):
        if symbol not in self.buffers:
            self.buffers[symbol] = deque(
                maxlen=WEBSOCKET_CONFIG["BUFFER_SIZE"]
            )
        
        async for message in websocket:
            try:
                data = json.loads(message)
                timestamp = time.time()
                
                data['received_at'] = timestamp
                self.buffers[symbol].append(data)
                
                if 'stream' in data:
                    latency = timestamp - (data.get('data', {}).get('E', timestamp * 1000) / 1000)
                    self.latency_stats[symbol] = latency
                    
                    if latency > WEBSOCKET_CONFIG["MAX_LATENCY"]:
                        logger.warning("high_websocket_latency", 
                                     symbol=symbol, 
                                     latency=latency)
                
                await self._dispatch_message(symbol, data)
                
            except json.JSONDecodeError as e:
                logger.error("json_decode_error", 
                           symbol=symbol, 
                           error=str(e))
            except Exception as e:
                logger.error("message_handling_error", 
                           symbol=symbol, 
                           error=str(e))
    
    async def _dispatch_message(self, symbol: str, data: Dict[str, Any]):
        if symbol in self.message_handlers:
            for handler in self.message_handlers[symbol]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error("message_handler_error", 
                               symbol=symbol, 
                               error=str(e))
    
    async def _handle_reconnect(self, symbol: str, attempt: int):
        delay = min(
            WEBSOCKET_CONFIG["RECONNECT_DELAY"] * (2 ** attempt),
            60
        )
        logger.info("websocket_reconnecting", 
                   symbol=symbol, 
                   attempt=attempt, 
                   delay=delay)
        await asyncio.sleep(delay)
    
    def register_handler(self, symbol: str, handler: Callable):
        if symbol not in self.message_handlers:
            self.message_handlers[symbol] = []
        self.message_handlers[symbol].append(handler)
        logger.info("handler_registered", symbol=symbol)
    
    def get_latest_data(self, symbol: str, count: int = 1) -> List[Dict[str, Any]]:
        if symbol in self.buffers:
            return list(self.buffers[symbol])[-count:]
        return []
    
    def get_latency(self, symbol: str) -> float:
        return self.latency_stats.get(symbol, 0.0)
    
    async def cleanup_old_data(self):
        while self.running:
            await asyncio.sleep(WEBSOCKET_CONFIG["MEMORY_CLEANUP_INTERVAL"])
            
            cutoff = time.time() - 86400
            for symbol in self.buffers:
                old_size = len(self.buffers[symbol])
                self.buffers[symbol] = deque(
                    [d for d in self.buffers[symbol] 
                     if d.get('received_at', 0) > cutoff],
                    maxlen=WEBSOCKET_CONFIG["BUFFER_SIZE"]
                )
                cleaned = old_size - len(self.buffers[symbol])
                if cleaned > 0:
                    logger.debug("buffer_cleaned", 
                               symbol=symbol, 
                               cleaned_count=cleaned)
    
    async def close(self):
        self.running = False
        for symbol, websocket in self.connections.items():
            await websocket.close()
            logger.info("websocket_closed", symbol=symbol)
        logger.info("websocket_manager_stopped")
