import aiohttp
import time
import hmac
import hashlib
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from config import BINANCE_CONFIG, TRADING_CONFIG
from utils.logger import get_logger
from utils.circuit_breaker import CircuitBreaker

logger = get_logger(__name__)

class BinanceClient:
    def __init__(self):
        self.api_key = BINANCE_CONFIG["API_KEY"]
        self.api_secret = BINANCE_CONFIG["API_SECRET"]
        self.testnet = BINANCE_CONFIG["TESTNET"]
        
        self.base_url = (BINANCE_CONFIG["TESTNET_BASE_URL"] 
                        if self.testnet 
                        else BINANCE_CONFIG["REST_BASE_URL"])
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.circuit_breaker = CircuitBreaker()
        
        logger.info("binance_client_initialized", testnet=self.testnet)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _request(self, 
                      method: str, 
                      endpoint: str, 
                      params: Optional[Dict[str, Any]] = None,
                      signed: bool = False) -> Dict[str, Any]:
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key} if self.api_key else {}
        
        session = await self._get_session()
        
        try:
            if method == 'GET':
                async with session.get(url, params=params, headers=headers) as response:
                    return await response.json()
            elif method == 'POST':
                async with session.post(url, params=params, headers=headers) as response:
                    return await response.json()
            elif method == 'DELETE':
                async with session.delete(url, params=params, headers=headers) as response:
                    return await response.json()
        except Exception as e:
            logger.error("api_request_failed", 
                        endpoint=endpoint, 
                        error=str(e))
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        if not TRADING_CONFIG["TRADING_ENABLED"]:
            return {
                'balances': [{'asset': 'USDT', 'free': '10000.0', 'locked': '0.0'}],
                'paper_trading': True
            }
        
        return await self._request(
            'GET',
            BINANCE_CONFIG["ENDPOINTS"]["account_info"],
            signed=True
        )
    
    async def get_balance(self) -> float:
        account = await self.get_account_info()
        
        if account.get('paper_trading'):
            return 10000.0
        
        for balance in account.get('balances', []):
            if balance['asset'] == 'USDT':
                return float(balance['free'])
        return 0.0
    
    async def create_order(self,
                          symbol: str,
                          side: str,
                          quantity: float,
                          price: Optional[float] = None,
                          order_type: str = 'MARKET') -> Dict[str, Any]:
        
        if not TRADING_CONFIG["TRADING_ENABLED"] or TRADING_CONFIG["PAPER_TRADING"]:
            logger.info("paper_trade_simulated",
                       symbol=symbol,
                       side=side,
                       quantity=quantity,
                       order_type=order_type)
            
            return {
                'orderId': int(time.time() * 1000),
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'price': price,
                'status': 'FILLED',
                'paper_trading': True
            }
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        if order_type == 'LIMIT' and price:
            params['price'] = price
            params['timeInForce'] = 'GTC'
        
        try:
            result = await self._request(
                'POST',
                BINANCE_CONFIG["ENDPOINTS"]["create_order"],
                params=params,
                signed=True
            )
            
            logger.info("order_created",
                       symbol=symbol,
                       side=side,
                       order_id=result.get('orderId'))
            
            return result
            
        except Exception as e:
            logger.error("order_creation_failed",
                        symbol=symbol,
                        side=side,
                        error=str(e))
            raise
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        if not TRADING_CONFIG["TRADING_ENABLED"] or TRADING_CONFIG["PAPER_TRADING"]:
            return {
                'orderId': order_id,
                'status': 'CANCELED',
                'paper_trading': True
            }
        
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        return await self._request(
            'DELETE',
            BINANCE_CONFIG["ENDPOINTS"]["cancel_order"],
            params=params,
            signed=True
        )
    
    async def get_symbol_price(self, symbol: str) -> float:
        result = await self._request(
            'GET',
            BINANCE_CONFIG["ENDPOINTS"]["ticker_24hr"],
            params={'symbol': symbol}
        )
        
        return float(result.get('lastPrice', 0))
    
    async def get_klines(self, 
                        symbol: str, 
                        interval: str = '1m', 
                        limit: int = 100) -> list:
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        return await self._request(
            'GET',
            BINANCE_CONFIG["ENDPOINTS"]["klines"],
            params=params
        )
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("binance_client_closed")
