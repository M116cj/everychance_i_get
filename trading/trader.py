import asyncio
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from trading.binance_client import BinanceClient
from core import (
    WebSocketManager, FeatureEngine, ModelManager,
    ColdStartEngine, RiskManager, ScoringEngine
)
from database.manager import DatabaseManager
from config import BINANCE_CONFIG, TRADING_CONFIG, MODEL_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class SelfLearningTrader:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.binance_client = BinanceClient()
        self.ws_manager = WebSocketManager()
        self.feature_engine = FeatureEngine()
        self.model_manager = ModelManager(self.db_manager)
        self.cold_start_engine = ColdStartEngine()
        self.risk_manager = RiskManager()
        self.scoring_engine = ScoringEngine()
        
        self.running = False
        self.open_trades: Dict[int, Dict[str, Any]] = {}
        
        logger.info("self_learning_trader_initialized")
    
    async def start(self):
        self.running = True
        
        symbols = BINANCE_CONFIG["SYMBOLS"]
        
        await self.ws_manager.connect(symbols)
        
        for symbol in symbols:
            self.ws_manager.register_handler(symbol, self._handle_market_data)
        
        asyncio.create_task(self._trading_loop())
        asyncio.create_task(self._monitor_positions())
        asyncio.create_task(self._periodic_training())
        asyncio.create_task(self.ws_manager.cleanup_old_data())
        
        logger.info("trader_started", symbols=symbols)
    
    async def _handle_market_data(self, data: Dict[str, Any]):
        if 'stream' not in data:
            return
        
        stream_name = data['stream']
        stream_data = data['data']
        
        symbol = stream_data.get('s', '').upper()
        
        if 'kline' in stream_name:
            kline = stream_data['k']
            if kline.get('x'):
                self.feature_engine.add_kline(symbol, kline)
        
        elif stream_name.endswith('@trade'):
            self.feature_engine.add_trade(symbol, stream_data)
    
    async def _trading_loop(self):
        while self.running:
            try:
                await asyncio.sleep(TRADING_CONFIG["TRADING_CYCLE_INTERVAL"])
                
                stats = self.db_manager.get_trade_statistics()
                self.cold_start_engine.update(stats['total_trades'])
                
                if len(self.open_trades) >= TRADING_CONFIG["MAX_CONCURRENT_POSITIONS"]:
                    continue
                
                for symbol in BINANCE_CONFIG["SYMBOLS"]:
                    if len(self.open_trades) >= TRADING_CONFIG["MAX_CONCURRENT_POSITIONS"]:
                        break
                    
                    signal = await self._generate_signal(symbol)
                    
                    if signal and signal['should_trade']:
                        await self._execute_trade(symbol, signal)
                
            except Exception as e:
                logger.error("trading_loop_error", error=str(e))
    
    async def _generate_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        features = self.feature_engine.calculate_features(symbol)
        
        if not features:
            return None
        
        prediction, confidence = self.model_manager.predict(features)
        
        thresholds = self.cold_start_engine.get_thresholds()
        
        exploration_prob = thresholds.get('exploration_prob', 0.0)
        if random.random() < exploration_prob:
            prediction = random.choice([0, 1])
            confidence = random.uniform(0.4, 0.7)
            logger.info("exploration_trade", symbol=symbol)
        
        signal_quality = (
            abs(features.get('market_structure_trend', 0)) * 0.3 +
            features.get('structure_integrity', 0) * 0.3 +
            features.get('trend_alignment', 0) * 0.2 +
            confidence * 0.2
        )
        
        should_trade = (
            confidence >= thresholds['min_confidence'] and
            signal_quality >= thresholds['signal_quality']
        )
        
        side = 'BUY' if prediction == 1 else 'SELL'
        
        return {
            'should_trade': should_trade,
            'side': side,
            'confidence': confidence,
            'signal_quality': signal_quality,
            'features': features,
            'prediction': prediction
        }
    
    async def _execute_trade(self, symbol: str, signal: Dict[str, Any]):
        try:
            account_balance = await self.binance_client.get_balance()
            current_price = await self.binance_client.get_symbol_price(symbol)
            
            max_leverage = self.cold_start_engine.get_max_leverage()
            leverage = min(
                signal['confidence'] * max_leverage,
                max_leverage
            )
            
            stop_loss_price = self.risk_manager.calculate_stop_loss(
                current_price,
                signal['side']
            )
            
            position_size = self.risk_manager.calculate_position_size(
                account_balance,
                current_price,
                stop_loss_price,
                leverage
            )
            
            risk_check = self.risk_manager.check_risk_limits(
                position_size,
                leverage,
                account_balance,
                len(self.open_trades)
            )
            
            if not risk_check['approved']:
                logger.warning("trade_rejected", 
                             symbol=symbol, 
                             reason=risk_check['reason'])
                return
            
            quantity = position_size / current_price
            
            order = await self.binance_client.create_order(
                symbol=symbol,
                side=signal['side'],
                quantity=quantity,
                order_type='MARKET'
            )
            
            take_profit_price = (
                current_price * 1.02 if signal['side'] == 'BUY'
                else current_price * 0.98
            )
            
            trade_data = {
                'symbol': symbol,
                'side': signal['side'],
                'entry_price': current_price,
                'quantity': quantity,
                'leverage': leverage,
                'stop_loss': stop_loss_price,
                'take_profit': take_profit_price,
                'confidence': signal['confidence'],
                'signal_quality': signal['signal_quality'],
                'features': signal['features'],
                'phase': self.cold_start_engine.get_phase().value,
                'model_version': self.model_manager.model_version,
                'status': 'OPEN'
            }
            
            trade = self.db_manager.save_trade(trade_data)
            
            self.open_trades[trade.id] = {
                'trade': trade,
                'order': order
            }
            
            logger.info("trade_opened",
                       trade_id=trade.id,
                       symbol=symbol,
                       side=signal['side'],
                       price=current_price,
                       confidence=signal['confidence'])
            
        except Exception as e:
            logger.error("trade_execution_failed", 
                        symbol=symbol, 
                        error=str(e))
    
    async def _monitor_positions(self):
        while self.running:
            try:
                await asyncio.sleep(TRADING_CONFIG["POSITION_MONITOR_INTERVAL"])
                
                for trade_id in list(self.open_trades.keys()):
                    trade_info = self.open_trades[trade_id]
                    trade = trade_info['trade']
                    
                    current_price = await self.binance_client.get_symbol_price(trade.symbol)
                    
                    should_close = False
                    close_reason = ""
                    
                    if trade.side == 'BUY':
                        if current_price >= trade.take_profit:
                            should_close = True
                            close_reason = "take_profit"
                        elif current_price <= trade.stop_loss:
                            should_close = True
                            close_reason = "stop_loss"
                    else:
                        if current_price <= trade.take_profit:
                            should_close = True
                            close_reason = "take_profit"
                        elif current_price >= trade.stop_loss:
                            should_close = True
                            close_reason = "stop_loss"
                    
                    if should_close:
                        await self._close_trade(trade_id, current_price, close_reason)
                
            except Exception as e:
                logger.error("position_monitoring_error", error=str(e))
    
    async def _close_trade(self, trade_id: int, exit_price: float, reason: str):
        if trade_id not in self.open_trades:
            return
        
        trade_info = self.open_trades[trade_id]
        trade = trade_info['trade']
        
        try:
            close_side = 'SELL' if trade.side == 'BUY' else 'BUY'
            
            await self.binance_client.create_order(
                symbol=trade.symbol,
                side=close_side,
                quantity=trade.quantity,
                order_type='MARKET'
            )
            
            if trade.side == 'BUY':
                pnl = (exit_price - trade.entry_price) * trade.quantity * trade.leverage
                pnl_pct = ((exit_price - trade.entry_price) / trade.entry_price) * trade.leverage
            else:
                pnl = (trade.entry_price - exit_price) * trade.quantity * trade.leverage
                pnl_pct = ((trade.entry_price - exit_price) / trade.entry_price) * trade.leverage
            
            self.db_manager.update_trade(trade_id, {
                'exit_price': exit_price,
                'exit_time': datetime.utcnow(),
                'pnl': pnl,
                'pnl_percentage': pnl_pct,
                'status': 'CLOSED'
            })
            
            self.risk_manager.update_daily_pnl(pnl)
            self.risk_manager.record_trade_result(pnl > 0)
            
            del self.open_trades[trade_id]
            
            logger.info("trade_closed",
                       trade_id=trade_id,
                       symbol=trade.symbol,
                       pnl=pnl,
                       pnl_pct=pnl_pct,
                       reason=reason)
            
        except Exception as e:
            logger.error("trade_closing_failed", 
                        trade_id=trade_id, 
                        error=str(e))
    
    async def _periodic_training(self):
        while self.running:
            try:
                await asyncio.sleep(300)
                
                trades = self.db_manager.get_trades(limit=500)
                
                if len(trades) >= MODEL_CONFIG["MIN_TRAINING_SAMPLES"]:
                    if len(trades) % MODEL_CONFIG["TRAINING_INTERVAL"] < 10:
                        logger.info("model_training_triggered", trade_count=len(trades))
                        result = self.model_manager.train(trades)
                        logger.info("model_training_completed", result=result)
                        
                        score = self.scoring_engine.score_trading_performance(trades)
                        logger.info("performance_score", score=score)
                
            except Exception as e:
                logger.error("periodic_training_error", error=str(e))
    
    async def stop(self):
        self.running = False
        
        await self.ws_manager.close()
        await self.binance_client.close()
        
        logger.info("trader_stopped")
    
    def get_status(self) -> Dict[str, Any]:
        stats = self.db_manager.get_trade_statistics()
        phase_info = self.cold_start_engine.get_phase_info()
        risk_status = self.risk_manager.get_risk_status()
        model_info = self.model_manager.get_model_info()
        
        return {
            'running': self.running,
            'open_positions': len(self.open_trades),
            'phase': phase_info,
            'statistics': stats,
            'risk': risk_status,
            'model': model_info
        }
