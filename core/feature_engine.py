import numpy as np
from typing import Dict, List, Any, Optional
from collections import deque

from config import FEATURE_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class FeatureEngine:
    def __init__(self):
        self.kline_buffers: Dict[str, deque] = {}
        self.trade_buffers: Dict[str, deque] = {}
        self.feature_cache: Dict[str, Dict[str, Any]] = {}
        
    def add_kline(self, symbol: str, kline_data: Dict[str, Any]):
        if symbol not in self.kline_buffers:
            self.kline_buffers[symbol] = deque(
                maxlen=FEATURE_CONFIG["MARKET_STRUCTURE_WINDOW"]
            )
        
        kline = {
            'timestamp': kline_data.get('t', 0),
            'open': float(kline_data.get('o', 0)),
            'high': float(kline_data.get('h', 0)),
            'low': float(kline_data.get('l', 0)),
            'close': float(kline_data.get('c', 0)),
            'volume': float(kline_data.get('v', 0)),
        }
        self.kline_buffers[symbol].append(kline)
    
    def add_trade(self, symbol: str, trade_data: Dict[str, Any]):
        if symbol not in self.trade_buffers:
            self.trade_buffers[symbol] = deque(
                maxlen=FEATURE_CONFIG["ORDER_FLOW_WINDOW"]
            )
        
        trade = {
            'timestamp': trade_data.get('T', 0),
            'price': float(trade_data.get('p', 0)),
            'quantity': float(trade_data.get('q', 0)),
            'is_buyer_maker': trade_data.get('m', False)
        }
        self.trade_buffers[symbol].append(trade)
    
    def calculate_features(self, symbol: str) -> Optional[Dict[str, Any]]:
        if symbol not in self.kline_buffers or len(self.kline_buffers[symbol]) < 30:
            return None
        
        klines = list(self.kline_buffers[symbol])
        
        features = {}
        
        features['market_structure_trend'] = self._calculate_market_structure(klines)
        features['order_blocks_count'] = self._count_order_blocks(klines)
        features['institutional_candle'] = self._detect_institutional_candle(klines)
        features['liquidity_grab'] = self._detect_liquidity_grab(klines)
        features['order_flow_value'] = self._calculate_order_flow(symbol)
        features['fvg_count'] = self._count_fair_value_gaps(klines)
        
        features['trend_alignment'] = self._calculate_trend_alignment(klines)
        features['swing_high_distance'] = self._calculate_swing_distance(klines, 'high')
        features['structure_integrity'] = self._calculate_structure_integrity(klines)
        features['institutional_participation'] = self._calculate_institutional_participation(klines)
        features['timeframe_convergence'] = self._calculate_timeframe_convergence(klines)
        features['liquidity_context'] = self._calculate_liquidity_context(klines)
        
        self.feature_cache[symbol] = features
        
        return features
    
    def _calculate_market_structure(self, klines: List[Dict]) -> float:
        if len(klines) < 10:
            return 0.0
        
        closes = [k['close'] for k in klines[-50:]]
        
        higher_highs = 0
        higher_lows = 0
        lower_highs = 0
        lower_lows = 0
        
        for i in range(10, len(closes)):
            if closes[i] > max(closes[i-10:i]):
                higher_highs += 1
            if closes[i] < min(closes[i-10:i]):
                lower_lows += 1
        
        if higher_highs > lower_lows:
            return min(higher_highs / len(closes) * 2, 1.0)
        else:
            return max(-lower_lows / len(closes) * 2, -1.0)
    
    def _count_order_blocks(self, klines: List[Dict]) -> int:
        if len(klines) < FEATURE_CONFIG["ORDER_BLOCKS_WINDOW"]:
            return 0
        
        order_blocks = 0
        recent_klines = klines[-FEATURE_CONFIG["ORDER_BLOCKS_WINDOW"]:]
        
        for i in range(3, len(recent_klines)):
            body = abs(recent_klines[i]['close'] - recent_klines[i]['open'])
            range_size = recent_klines[i]['high'] - recent_klines[i]['low']
            
            if range_size > 0 and body / range_size > 0.7:
                volume_ratio = recent_klines[i]['volume'] / np.mean(
                    [k['volume'] for k in recent_klines[max(0, i-10):i]]
                )
                if volume_ratio > 1.5:
                    order_blocks += 1
        
        return order_blocks
    
    def _detect_institutional_candle(self, klines: List[Dict]) -> bool:
        if len(klines) < 5:
            return False
        
        latest = klines[-1]
        avg_volume = np.mean([k['volume'] for k in klines[-20:-1]])
        
        body = abs(latest['close'] - latest['open'])
        range_size = latest['high'] - latest['low']
        
        is_large_body = range_size > 0 and body / range_size > 0.8
        is_high_volume = latest['volume'] > avg_volume * 2
        
        return is_large_body and is_high_volume
    
    def _detect_liquidity_grab(self, klines: List[Dict]) -> bool:
        if len(klines) < 10:
            return False
        
        recent = klines[-10:]
        latest = klines[-1]
        
        prev_high = max(k['high'] for k in recent[:-1])
        prev_low = min(k['low'] for k in recent[:-1])
        
        grabbed_high = latest['high'] > prev_high and latest['close'] < prev_high
        grabbed_low = latest['low'] < prev_low and latest['close'] > prev_low
        
        return grabbed_high or grabbed_low
    
    def _calculate_order_flow(self, symbol: str) -> float:
        if symbol not in self.trade_buffers or len(self.trade_buffers[symbol]) < 100:
            return 0.0
        
        trades = list(self.trade_buffers[symbol])[-1000:]
        
        buy_volume = sum(t['quantity'] for t in trades if not t['is_buyer_maker'])
        sell_volume = sum(t['quantity'] for t in trades if t['is_buyer_maker'])
        
        total_volume = buy_volume + sell_volume
        if total_volume == 0:
            return 0.0
        
        return (buy_volume - sell_volume) / total_volume
    
    def _count_fair_value_gaps(self, klines: List[Dict]) -> int:
        if len(klines) < FEATURE_CONFIG["FVG_WINDOW"]:
            return 0
        
        fvg_count = 0
        recent = klines[-FEATURE_CONFIG["FVG_WINDOW"]:]
        
        for i in range(2, len(recent)):
            gap_up = recent[i]['low'] > recent[i-2]['high']
            gap_down = recent[i]['high'] < recent[i-2]['low']
            
            if gap_up or gap_down:
                fvg_count += 1
        
        return fvg_count
    
    def _calculate_trend_alignment(self, klines: List[Dict]) -> float:
        if len(klines) < 50:
            return 0.0
        
        short_ma = np.mean([k['close'] for k in klines[-10:]])
        medium_ma = np.mean([k['close'] for k in klines[-25:]])
        long_ma = np.mean([k['close'] for k in klines[-50:]])
        
        if short_ma > medium_ma > long_ma:
            return 1.0
        elif short_ma < medium_ma < long_ma:
            return -1.0
        else:
            return 0.0
    
    def _calculate_swing_distance(self, klines: List[Dict], swing_type: str) -> float:
        if len(klines) < 20:
            return 0.0
        
        recent = klines[-20:]
        current_price = recent[-1]['close']
        
        if swing_type == 'high':
            swing_point = max(k['high'] for k in recent)
        else:
            swing_point = min(k['low'] for k in recent)
        
        if swing_point == 0:
            return 0.0
        
        return abs(current_price - swing_point) / swing_point
    
    def _calculate_structure_integrity(self, klines: List[Dict]) -> float:
        if len(klines) < 30:
            return 0.0
        
        trend = self._calculate_market_structure(klines)
        
        recent = klines[-30:]
        breaks = 0
        
        for i in range(10, len(recent)):
            if trend > 0:
                if recent[i]['low'] < min(k['low'] for k in recent[i-10:i]):
                    breaks += 1
            else:
                if recent[i]['high'] > max(k['high'] for k in recent[i-10:i]):
                    breaks += 1
        
        return max(0.0, 1.0 - (breaks / 10))
    
    def _calculate_institutional_participation(self, klines: List[Dict]) -> float:
        if len(klines) < 20:
            return 0.0
        
        recent = klines[-20:]
        avg_volume = np.mean([k['volume'] for k in recent])
        
        high_volume_candles = sum(
            1 for k in recent if k['volume'] > avg_volume * 1.5
        )
        
        return high_volume_candles / len(recent)
    
    def _calculate_timeframe_convergence(self, klines: List[Dict]) -> float:
        if len(klines) < 60:
            return 0.0
        
        tf1_trend = self._calculate_market_structure(klines[-15:])
        tf2_trend = self._calculate_market_structure(klines[-30:])
        tf3_trend = self._calculate_market_structure(klines[-60:])
        
        trends = [tf1_trend, tf2_trend, tf3_trend]
        
        if all(t > 0 for t in trends):
            return 1.0
        elif all(t < 0 for t in trends):
            return -1.0
        else:
            return 0.0
    
    def _calculate_liquidity_context(self, klines: List[Dict]) -> float:
        if len(klines) < 30:
            return 0.0
        
        recent = klines[-30:]
        
        avg_range = np.mean([k['high'] - k['low'] for k in recent])
        latest_range = recent[-1]['high'] - recent[-1]['low']
        
        if avg_range == 0:
            return 0.0
        
        return latest_range / avg_range
    
    def get_cached_features(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self.feature_cache.get(symbol)
