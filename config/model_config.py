MODEL_CONFIG = {
    "MODEL_TYPE": "XGBoost",
    "TRAINING_INTERVAL": 100,
    "MIN_TRAINING_SAMPLES": 50,
    "TRAINING_VALIDATION_SPLIT": 0.2,
    
    "XGB_PARAMS": {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "random_state": 42
    },
    
    "FEATURE_NAMES": [
        'market_structure_trend', 'order_blocks_count', 'institutional_candle',
        'liquidity_grab', 'order_flow_value', 'fvg_count', 'trend_alignment',
        'swing_high_distance', 'structure_integrity', 'institutional_participation',
        'timeframe_convergence', 'liquidity_context'
    ],
    
    "MODEL_SAVE_INTERVAL": 10,
    "MAX_MODEL_VERSIONS": 10,
}
