from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    leverage = Column(Float, default=1.0)
    
    stop_loss = Column(Float)
    take_profit = Column(Float)
    
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime)
    
    pnl = Column(Float, default=0.0)
    pnl_percentage = Column(Float, default=0.0)
    status = Column(String(20), default='OPEN')
    
    confidence = Column(Float)
    signal_quality = Column(Float)
    
    features = Column(JSON)
    
    phase = Column(String(20))
    model_version = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FeatureSnapshot(Base):
    __tablename__ = 'feature_snapshots'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    market_structure_trend = Column(Float)
    order_blocks_count = Column(Integer)
    institutional_candle = Column(Boolean)
    liquidity_grab = Column(Boolean)
    order_flow_value = Column(Float)
    fvg_count = Column(Integer)
    trend_alignment = Column(Float)
    swing_high_distance = Column(Float)
    structure_integrity = Column(Float)
    institutional_participation = Column(Float)
    timeframe_convergence = Column(Float)
    liquidity_context = Column(Float)
    
    additional_features = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelCheckpoint(Base):
    __tablename__ = 'model_checkpoints'
    
    id = Column(Integer, primary_key=True)
    version = Column(String(50), unique=True, nullable=False)
    model_type = Column(String(50), default='XGBoost')
    
    training_trades = Column(Integer)
    train_score = Column(Float)
    val_score = Column(Float)
    
    feature_importance = Column(JSON)
    hyperparameters = Column(JSON)
    
    model_path = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemState(Base):
    __tablename__ = 'system_state'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
