from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from config import RISK_CONFIG, TRADING_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class RiskManager:
    def __init__(self):
        self.daily_pnl = 0.0
        self.daily_reset_time = datetime.utcnow()
        self.consecutive_losses = 0
        self.circuit_breaker_active = False
        self.circuit_breaker_until = None
        
        logger.info("risk_manager_initialized")
    
    def check_risk_limits(self, 
                         position_size: float,
                         leverage: float,
                         account_balance: float,
                         open_positions: int) -> Dict[str, Any]:
        
        self._reset_daily_if_needed()
        
        if self.circuit_breaker_active:
            if datetime.utcnow() < self.circuit_breaker_until:
                return {
                    'approved': False,
                    'reason': 'circuit_breaker_active',
                    'cooldown_remaining': (self.circuit_breaker_until - datetime.utcnow()).seconds
                }
            else:
                self._reset_circuit_breaker()
        
        if abs(self.daily_pnl / account_balance) >= RISK_CONFIG["DAILY_LOSS_LIMIT"]:
            return {
                'approved': False,
                'reason': 'daily_loss_limit_reached',
                'daily_pnl': self.daily_pnl,
                'limit': RISK_CONFIG["DAILY_LOSS_LIMIT"]
            }
        
        if open_positions >= TRADING_CONFIG["MAX_CONCURRENT_POSITIONS"]:
            return {
                'approved': False,
                'reason': 'max_positions_reached',
                'current': open_positions,
                'max': TRADING_CONFIG["MAX_CONCURRENT_POSITIONS"]
            }
        
        if leverage > RISK_CONFIG["MAX_LEVERAGE"]:
            return {
                'approved': False,
                'reason': 'leverage_too_high',
                'requested': leverage,
                'max': RISK_CONFIG["MAX_LEVERAGE"]
            }
        
        risk_amount = position_size * leverage
        if risk_amount / account_balance > RISK_CONFIG["SINGLE_TRADE_RISK"]:
            return {
                'approved': False,
                'reason': 'position_risk_too_high',
                'risk_percentage': risk_amount / account_balance,
                'max': RISK_CONFIG["SINGLE_TRADE_RISK"]
            }
        
        return {
            'approved': True,
            'message': 'risk_check_passed'
        }
    
    def calculate_position_size(self,
                               account_balance: float,
                               entry_price: float,
                               stop_loss_price: float,
                               leverage: float) -> float:
        
        risk_amount = account_balance * RISK_CONFIG["SINGLE_TRADE_RISK"]
        
        price_risk = abs(entry_price - stop_loss_price) / entry_price
        
        if price_risk == 0:
            return TRADING_CONFIG["MIN_POSITION_SIZE"]
        
        position_size = (risk_amount / price_risk) / leverage
        
        position_size = max(position_size, TRADING_CONFIG["MIN_POSITION_SIZE"])
        position_size = min(position_size, TRADING_CONFIG["MAX_POSITION_SIZE"])
        
        return position_size
    
    def calculate_stop_loss(self,
                           entry_price: float,
                           side: str,
                           atr: Optional[float] = None) -> float:
        
        if atr:
            stop_distance = atr * 2
        else:
            stop_distance = entry_price * RISK_CONFIG["HARD_STOP_LOSS"]
        
        if side == 'BUY':
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def update_daily_pnl(self, pnl: float):
        self._reset_daily_if_needed()
        
        old_pnl = self.daily_pnl
        self.daily_pnl += pnl
        
        logger.info("daily_pnl_updated", 
                   old_pnl=old_pnl, 
                   new_pnl=self.daily_pnl, 
                   change=pnl)
    
    def record_trade_result(self, is_win: bool):
        if is_win:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            
            if (RISK_CONFIG["CIRCUIT_BREAKER_ENABLED"] and 
                self.consecutive_losses >= RISK_CONFIG["MAX_CONSECUTIVE_LOSSES"]):
                self._activate_circuit_breaker()
    
    def _activate_circuit_breaker(self):
        self.circuit_breaker_active = True
        self.circuit_breaker_until = datetime.utcnow() + timedelta(
            seconds=RISK_CONFIG["COOLDOWN_PERIOD"]
        )
        
        logger.warning("circuit_breaker_activated",
                      consecutive_losses=self.consecutive_losses,
                      cooldown_period=RISK_CONFIG["COOLDOWN_PERIOD"])
    
    def _reset_circuit_breaker(self):
        self.circuit_breaker_active = False
        self.circuit_breaker_until = None
        self.consecutive_losses = 0
        
        logger.info("circuit_breaker_reset")
    
    def _reset_daily_if_needed(self):
        if datetime.utcnow() - self.daily_reset_time > timedelta(days=1):
            logger.info("daily_pnl_reset", old_pnl=self.daily_pnl)
            self.daily_pnl = 0.0
            self.daily_reset_time = datetime.utcnow()
    
    def get_risk_status(self) -> Dict[str, Any]:
        return {
            'daily_pnl': self.daily_pnl,
            'consecutive_losses': self.consecutive_losses,
            'circuit_breaker_active': self.circuit_breaker_active,
            'circuit_breaker_until': self.circuit_breaker_until.isoformat() if self.circuit_breaker_until else None
        }
