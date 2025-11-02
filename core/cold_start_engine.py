from typing import Dict, Any
from enum import Enum

from config import LEARNING_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class Phase(Enum):
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation" 
    MATURE = "mature"

class ColdStartEngine:
    def __init__(self):
        self.current_phase = Phase.EXPLORATION
        self.trade_count = 0
        self.phase_thresholds = {
            Phase.EXPLORATION: LEARNING_CONFIG["EXPLORATION_PHASE_TRADES"],
            Phase.EXPLOITATION: LEARNING_CONFIG["EXPLOITATION_PHASE_TRADES"],
        }
        
        logger.info("cold_start_engine_initialized", phase=self.current_phase.value)
    
    def update(self, trade_count: int):
        self.trade_count = trade_count
        old_phase = self.current_phase
        
        if trade_count >= self.phase_thresholds[Phase.EXPLOITATION]:
            self.current_phase = Phase.MATURE
        elif trade_count >= self.phase_thresholds[Phase.EXPLORATION]:
            self.current_phase = Phase.EXPLOITATION
        else:
            self.current_phase = Phase.EXPLORATION
        
        if old_phase != self.current_phase:
            logger.info("phase_transition",
                       old_phase=old_phase.value,
                       new_phase=self.current_phase.value,
                       trade_count=trade_count)
    
    def get_phase(self) -> Phase:
        return self.current_phase
    
    def get_thresholds(self) -> Dict[str, float]:
        if self.current_phase == Phase.EXPLORATION:
            return {
                'min_win_rate': LEARNING_CONFIG["BOOTSTRAP_MIN_WIN_RATE"],
                'min_confidence': LEARNING_CONFIG["BOOTSTRAP_MIN_CONFIDENCE"],
                'signal_quality': LEARNING_CONFIG["BOOTSTRAP_SIGNAL_QUALITY"],
                'exploration_prob': LEARNING_CONFIG["EXPLORATION_PROBABILITY"]
            }
        elif self.current_phase == Phase.EXPLOITATION:
            return {
                'min_win_rate': (LEARNING_CONFIG["BOOTSTRAP_MIN_WIN_RATE"] + 
                               LEARNING_CONFIG["MATURE_MIN_WIN_RATE"]) / 2,
                'min_confidence': (LEARNING_CONFIG["BOOTSTRAP_MIN_CONFIDENCE"] + 
                                 LEARNING_CONFIG["MATURE_MIN_CONFIDENCE"]) / 2,
                'signal_quality': (LEARNING_CONFIG["BOOTSTRAP_SIGNAL_QUALITY"] + 
                                 LEARNING_CONFIG["MATURE_SIGNAL_QUALITY"]) / 2,
                'exploration_prob': LEARNING_CONFIG["EXPLORATION_PROBABILITY"] * 0.5
            }
        else:
            return {
                'min_win_rate': LEARNING_CONFIG["MATURE_MIN_WIN_RATE"],
                'min_confidence': LEARNING_CONFIG["MATURE_MIN_CONFIDENCE"],
                'signal_quality': LEARNING_CONFIG["MATURE_SIGNAL_QUALITY"],
                'exploration_prob': 0.0
            }
    
    def get_max_leverage(self) -> float:
        from config import RISK_CONFIG
        
        if self.current_phase == Phase.EXPLORATION:
            return RISK_CONFIG["BOOTSTRAP_MAX_LEVERAGE"]
        elif self.current_phase == Phase.EXPLOITATION:
            return min(
                RISK_CONFIG["BOOTSTRAP_MAX_LEVERAGE"] * 5,
                RISK_CONFIG["MAX_LEVERAGE"]
            )
        else:
            return RISK_CONFIG["MAX_LEVERAGE"]
    
    def get_phase_info(self) -> Dict[str, Any]:
        return {
            'phase': self.current_phase.value,
            'trade_count': self.trade_count,
            'thresholds': self.get_thresholds(),
            'max_leverage': self.get_max_leverage()
        }
