from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    market = Column(String, default="NSE")  # NSE, BSE, CRYPTO
    direction = Column(String, nullable=False)  # BUY, SELL
    
    # Trade Levels
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_1 = Column(Float, nullable=False)
    target_2 = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=False)  # target / sl
    
    # Scoring & Classification (Layer 3 & Layer 6)
    confidence_score = Column(Float, nullable=False)  # 0-100
    market_regime = Column(String, nullable=False)  # trending, ranging, breakout, etc.
    
    # Metadata & Context
    status = Column(String, default="active")  # active, triggered, expired, cancelled
    invalidation_conditions = Column(JSON, default=list)
    explanation = Column(String, nullable=True)  # Layer 9 text explanation
    
    # Complete 10-layer telemetry snapshot for debugging/analytics
    layers_telemetry = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
