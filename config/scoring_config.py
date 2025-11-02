SCORING_CONFIG = {
    "WEIGHTS": {
        "WIN_RATE": 0.35,
        "CONFIDENCE_ACCURACY": 0.25, 
        "PROFIT_FACTOR": 0.20,
        "CONSISTENCY": 0.15,
        "RISK_ADJUSTMENT": 0.05
    },
    
    "THRESHOLDS": {
        "EXCELLENT": 90,
        "GOOD": 75,
        "FAIR": 60,
        "POOR": 40
    },
    
    "BENCHMARKS": {
        "MIN_WIN_RATE": 0.50,
        "TARGET_WIN_RATE": 0.65,
        "MIN_PROFIT_FACTOR": 1.2,
        "TARGET_PROFIT_FACTOR": 2.0,
        "MAX_DRAWDOWN": 0.10
    },
    
    "ALERT_THRESHOLDS": {
        "CRITICAL_SCORE": 50,
        "WARNING_SCORE": 60,
        "LOW_WIN_RATE": 0.4,
        "NEGATIVE_PROFIT_FACTOR": 1.0
    }
}
