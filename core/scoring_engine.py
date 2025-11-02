from typing import Dict, Any, List
import numpy as np

from config import SCORING_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class ScoringEngine:
    def __init__(self):
        self.weights = SCORING_CONFIG["WEIGHTS"]
        self.thresholds = SCORING_CONFIG["THRESHOLDS"]
        self.benchmarks = SCORING_CONFIG["BENCHMARKS"]
        
        logger.info("scoring_engine_initialized")
    
    def score_trading_performance(self, trades: List[Any]) -> Dict[str, Any]:
        if not trades:
            return self._empty_score()
        
        closed_trades = [t for t in trades if t.status == 'CLOSED']
        
        if not closed_trades:
            return self._empty_score()
        
        win_rate_score = self._score_win_rate(closed_trades)
        confidence_score = self._score_confidence_accuracy(closed_trades)
        profit_factor_score = self._score_profit_factor(closed_trades)
        consistency_score = self._score_consistency(closed_trades)
        risk_adjusted_score = self._score_risk_adjustment(closed_trades)
        
        total_score = (
            win_rate_score * self.weights["WIN_RATE"] +
            confidence_score * self.weights["CONFIDENCE_ACCURACY"] +
            profit_factor_score * self.weights["PROFIT_FACTOR"] +
            consistency_score * self.weights["CONSISTENCY"] +
            risk_adjusted_score * self.weights["RISK_ADJUSTMENT"]
        )
        
        rating = self._get_rating(total_score)
        suggestions = self._generate_suggestions(
            win_rate_score, 
            confidence_score,
            profit_factor_score,
            consistency_score,
            risk_adjusted_score
        )
        
        return {
            'total_score': total_score,
            'rating': rating,
            'component_scores': {
                'win_rate': win_rate_score,
                'confidence_accuracy': confidence_score,
                'profit_factor': profit_factor_score,
                'consistency': consistency_score,
                'risk_adjustment': risk_adjusted_score
            },
            'suggestions': suggestions,
            'trade_count': len(closed_trades)
        }
    
    def _score_win_rate(self, trades: List[Any]) -> float:
        wins = sum(1 for t in trades if t.pnl > 0)
        win_rate = wins / len(trades)
        
        target = self.benchmarks["TARGET_WIN_RATE"]
        min_rate = self.benchmarks["MIN_WIN_RATE"]
        
        if win_rate >= target:
            return 100.0
        elif win_rate >= min_rate:
            return 50 + ((win_rate - min_rate) / (target - min_rate)) * 50
        else:
            return (win_rate / min_rate) * 50
    
    def _score_confidence_accuracy(self, trades: List[Any]) -> float:
        if not any(t.confidence for t in trades):
            return 50.0
        
        accurate_predictions = 0
        total_with_confidence = 0
        
        for trade in trades:
            if trade.confidence:
                total_with_confidence += 1
                
                was_profitable = trade.pnl > 0
                predicted_profitable = trade.confidence > 0.5
                
                if was_profitable == predicted_profitable:
                    accurate_predictions += 1
        
        if total_with_confidence == 0:
            return 50.0
        
        accuracy = accurate_predictions / total_with_confidence
        return accuracy * 100
    
    def _score_profit_factor(self, trades: List[Any]) -> float:
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        
        if gross_loss == 0:
            return 100.0 if gross_profit > 0 else 0.0
        
        profit_factor = gross_profit / gross_loss
        
        target = self.benchmarks["TARGET_PROFIT_FACTOR"]
        min_factor = self.benchmarks["MIN_PROFIT_FACTOR"]
        
        if profit_factor >= target:
            return 100.0
        elif profit_factor >= min_factor:
            return 50 + ((profit_factor - min_factor) / (target - min_factor)) * 50
        else:
            return (profit_factor / min_factor) * 50
    
    def _score_consistency(self, trades: List[Any]) -> float:
        if len(trades) < 10:
            return 50.0
        
        pnls = [t.pnl for t in trades]
        
        mean_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        
        if std_pnl == 0:
            return 100.0 if mean_pnl > 0 else 0.0
        
        cv = abs(std_pnl / mean_pnl) if mean_pnl != 0 else float('inf')
        
        if cv < 0.5:
            return 100.0
        elif cv < 1.5:
            return 100 - ((cv - 0.5) / 1.0) * 50
        else:
            return max(0, 50 - ((cv - 1.5) / 2.0) * 50)
    
    def _score_risk_adjustment(self, trades: List[Any]) -> float:
        returns = [t.pnl_percentage for t in trades if t.pnl_percentage]
        
        if not returns or len(returns) < 5:
            return 50.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 100.0 if avg_return > 0 else 0.0
        
        sharpe_like = avg_return / std_return
        
        if sharpe_like > 2.0:
            return 100.0
        elif sharpe_like > 1.0:
            return 50 + (sharpe_like - 1.0) * 50
        elif sharpe_like > 0:
            return sharpe_like * 50
        else:
            return 0.0
    
    def _get_rating(self, score: float) -> str:
        if score >= self.thresholds["EXCELLENT"]:
            return "EXCELLENT"
        elif score >= self.thresholds["GOOD"]:
            return "GOOD"
        elif score >= self.thresholds["FAIR"]:
            return "FAIR"
        elif score >= self.thresholds["POOR"]:
            return "POOR"
        else:
            return "VERY_POOR"
    
    def _generate_suggestions(self, *scores) -> List[str]:
        suggestions = []
        
        win_rate, confidence, profit_factor, consistency, risk = scores
        
        if win_rate < 60:
            suggestions.append("Improve signal quality - current win rate below target")
        
        if confidence < 60:
            suggestions.append("Model predictions not aligned with outcomes - retrain model")
        
        if profit_factor < 60:
            suggestions.append("Profit factor below target - review risk/reward ratios")
        
        if consistency < 60:
            suggestions.append("High variance in returns - standardize position sizing")
        
        if risk < 60:
            suggestions.append("Risk-adjusted returns suboptimal - tighten stop losses")
        
        return suggestions
    
    def _empty_score(self) -> Dict[str, Any]:
        return {
            'total_score': 0.0,
            'rating': 'NO_DATA',
            'component_scores': {
                'win_rate': 0.0,
                'confidence_accuracy': 0.0,
                'profit_factor': 0.0,
                'consistency': 0.0,
                'risk_adjustment': 0.0
            },
            'suggestions': ['Insufficient trade data for scoring'],
            'trade_count': 0
        }
