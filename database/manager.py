import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from database.models import Base, Trade, FeatureSnapshot, ModelCheckpoint, SystemState
from config import PERSISTENCE_CONFIG, SYSTEM_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    def __init__(self):
        os.makedirs(SYSTEM_CONFIG["DATA_PATH"], exist_ok=True)
        
        self.engine = create_engine(
            PERSISTENCE_CONFIG["DATABASE_URL"],
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info("database_initialized", db_url=PERSISTENCE_CONFIG["DATABASE_URL"])
    
    @contextmanager
    def get_session(self) -> Session:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            session.close()
    
    def save_trade(self, trade_data: Dict[str, Any]) -> Trade:
        with self.get_session() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            session.flush()
            logger.info("trade_saved", trade_id=trade.id, symbol=trade.symbol)
            return trade
    
    def update_trade(self, trade_id: int, updates: Dict[str, Any]) -> Optional[Trade]:
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                for key, value in updates.items():
                    setattr(trade, key, value)
                trade.updated_at = datetime.utcnow()
                logger.info("trade_updated", trade_id=trade_id)
                return trade
            return None
    
    def get_trades(self, limit: int = 100, status: Optional[str] = None) -> List[Trade]:
        with self.get_session() as session:
            query = session.query(Trade)
            if status:
                query = query.filter(Trade.status == status)
            return query.order_by(desc(Trade.created_at)).limit(limit).all()
    
    def save_feature_snapshot(self, snapshot_data: Dict[str, Any]) -> FeatureSnapshot:
        with self.get_session() as session:
            snapshot = FeatureSnapshot(**snapshot_data)
            session.add(snapshot)
            session.flush()
            return snapshot
    
    def get_recent_features(self, symbol: str, limit: int = 100) -> List[FeatureSnapshot]:
        with self.get_session() as session:
            return session.query(FeatureSnapshot).filter(
                FeatureSnapshot.symbol == symbol
            ).order_by(desc(FeatureSnapshot.timestamp)).limit(limit).all()
    
    def save_model_checkpoint(self, checkpoint_data: Dict[str, Any]) -> ModelCheckpoint:
        with self.get_session() as session:
            checkpoint = ModelCheckpoint(**checkpoint_data)
            session.add(checkpoint)
            session.flush()
            logger.info("model_checkpoint_saved", version=checkpoint.version)
            return checkpoint
    
    def get_latest_model_checkpoint(self) -> Optional[ModelCheckpoint]:
        with self.get_session() as session:
            return session.query(ModelCheckpoint).order_by(
                desc(ModelCheckpoint.created_at)
            ).first()
    
    def set_system_state(self, key: str, value: Any):
        with self.get_session() as session:
            state = session.query(SystemState).filter(SystemState.key == key).first()
            if state:
                state.value = value
                state.updated_at = datetime.utcnow()
            else:
                state = SystemState(key=key, value=value)
                session.add(state)
            logger.debug("system_state_updated", key=key)
    
    def get_system_state(self, key: str) -> Optional[Any]:
        with self.get_session() as session:
            state = session.query(SystemState).filter(SystemState.key == key).first()
            return state.value if state else None
    
    def cleanup_old_data(self):
        cutoff_date = datetime.utcnow() - timedelta(days=PERSISTENCE_CONFIG["MAX_BACKUP_AGE"])
        
        with self.get_session() as session:
            old_snapshots = session.query(FeatureSnapshot).filter(
                FeatureSnapshot.created_at < cutoff_date
            ).delete()
            
            logger.info("database_cleanup", snapshots_deleted=old_snapshots)
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        with self.get_session() as session:
            total_trades = session.query(Trade).count()
            closed_trades = session.query(Trade).filter(Trade.status == 'CLOSED').all()
            
            if not closed_trades:
                return {
                    'total_trades': total_trades,
                    'closed_trades': 0,
                    'win_rate': 0.0,
                    'avg_pnl': 0.0,
                    'total_pnl': 0.0
                }
            
            wins = sum(1 for t in closed_trades if t.pnl > 0)
            win_rate = wins / len(closed_trades) if closed_trades else 0
            
            total_pnl = sum(t.pnl for t in closed_trades)
            avg_pnl = total_pnl / len(closed_trades) if closed_trades else 0
            
            return {
                'total_trades': total_trades,
                'closed_trades': len(closed_trades),
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'total_pnl': total_pnl,
                'wins': wins,
                'losses': len(closed_trades) - wins
            }
