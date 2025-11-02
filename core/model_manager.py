import os
import pickle
import numpy as np
import xgboost as xgb
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import train_test_split

from config import MODEL_CONFIG, SYSTEM_CONFIG
from database.manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)

class ModelManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.model: Optional[xgb.XGBClassifier] = None
        self.model_version: Optional[str] = None
        self.feature_importance: Dict[str, float] = {}
        
        os.makedirs(SYSTEM_CONFIG["MODELS_PATH"], exist_ok=True)
        
        self._load_latest_model()
    
    def _load_latest_model(self):
        checkpoint = self.db_manager.get_latest_model_checkpoint()
        
        if checkpoint and os.path.exists(checkpoint.model_path):
            try:
                with open(checkpoint.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.model_version = checkpoint.version
                self.feature_importance = checkpoint.feature_importance
                logger.info("model_loaded", version=self.model_version)
            except Exception as e:
                logger.error("model_load_failed", error=str(e))
                self._initialize_model()
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        self.model = xgb.XGBClassifier(**MODEL_CONFIG["XGB_PARAMS"])
        self.model_version = f"v0.0.0_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info("model_initialized", version=self.model_version)
    
    def train(self, trades: List[Any]) -> Dict[str, Any]:
        if len(trades) < MODEL_CONFIG["MIN_TRAINING_SAMPLES"]:
            logger.warning("insufficient_training_data", 
                         required=MODEL_CONFIG["MIN_TRAINING_SAMPLES"],
                         available=len(trades))
            return {"status": "insufficient_data"}
        
        X, y = self._prepare_training_data(trades)
        
        if len(X) < MODEL_CONFIG["MIN_TRAINING_SAMPLES"]:
            return {"status": "insufficient_valid_data"}
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, 
            test_size=MODEL_CONFIG["TRAINING_VALIDATION_SPLIT"],
            random_state=42
        )
        
        try:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
            
            train_score = self.model.score(X_train, y_train)
            val_score = self.model.score(X_val, y_val)
            
            self._update_feature_importance()
            
            self.model_version = f"v1.{len(trades)//100}.0_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            model_path = os.path.join(
                SYSTEM_CONFIG["MODELS_PATH"],
                f"model_{self.model_version}.pkl"
            )
            
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            self.db_manager.save_model_checkpoint({
                'version': self.model_version,
                'training_trades': len(trades),
                'train_score': train_score,
                'val_score': val_score,
                'feature_importance': self.feature_importance,
                'hyperparameters': MODEL_CONFIG["XGB_PARAMS"],
                'model_path': model_path
            })
            
            logger.info("model_trained",
                       version=self.model_version,
                       train_score=train_score,
                       val_score=val_score,
                       samples=len(trades))
            
            return {
                "status": "success",
                "version": self.model_version,
                "train_score": train_score,
                "val_score": val_score,
                "samples": len(trades)
            }
            
        except Exception as e:
            logger.error("model_training_failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    def _prepare_training_data(self, trades: List[Any]) -> Tuple[np.ndarray, np.ndarray]:
        X = []
        y = []
        
        for trade in trades:
            if trade.features and trade.status == 'CLOSED':
                feature_vector = [
                    trade.features.get('market_structure_trend', 0),
                    trade.features.get('order_blocks_count', 0),
                    1 if trade.features.get('institutional_candle', False) else 0,
                    1 if trade.features.get('liquidity_grab', False) else 0,
                    trade.features.get('order_flow_value', 0),
                    trade.features.get('fvg_count', 0),
                    trade.features.get('trend_alignment', 0),
                    trade.features.get('swing_high_distance', 0),
                    trade.features.get('structure_integrity', 0),
                    trade.features.get('institutional_participation', 0),
                    trade.features.get('timeframe_convergence', 0),
                    trade.features.get('liquidity_context', 0),
                ]
                
                X.append(feature_vector)
                y.append(1 if trade.pnl > 0 else 0)
        
        return np.array(X), np.array(y)
    
    def _update_feature_importance(self):
        if hasattr(self.model, 'feature_importances_'):
            feature_names = MODEL_CONFIG["FEATURE_NAMES"]
            importances = self.model.feature_importances_
            
            self.feature_importance = {
                name: float(importance)
                for name, importance in zip(feature_names, importances)
            }
    
    def predict(self, features: Dict[str, Any]) -> Tuple[int, float]:
        if self.model is None:
            return 0, 0.5
        
        feature_vector = np.array([[
            features.get('market_structure_trend', 0),
            features.get('order_blocks_count', 0),
            1 if features.get('institutional_candle', False) else 0,
            1 if features.get('liquidity_grab', False) else 0,
            features.get('order_flow_value', 0),
            features.get('fvg_count', 0),
            features.get('trend_alignment', 0),
            features.get('swing_high_distance', 0),
            features.get('structure_integrity', 0),
            features.get('institutional_participation', 0),
            features.get('timeframe_convergence', 0),
            features.get('liquidity_context', 0),
        ]])
        
        try:
            prediction = self.model.predict(feature_vector)[0]
            probability = self.model.predict_proba(feature_vector)[0]
            confidence = max(probability)
            
            return int(prediction), float(confidence)
        except Exception as e:
            logger.error("prediction_failed", error=str(e))
            return 0, 0.5
    
    def get_feature_importance(self) -> Dict[str, float]:
        return self.feature_importance
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'version': self.model_version,
            'feature_importance': self.feature_importance,
            'hyperparameters': MODEL_CONFIG["XGB_PARAMS"]
        }
