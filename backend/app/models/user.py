from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Onboarding & Trading Settings (Layer 2 - Trader Profile Engine)
    trading_style = Column(String, default="scalp")  # scalp, day_trade, swing
    risk_appetite = Column(String, default="medium")  # low, medium, high
    experience_level = Column(String, default="beginner")  # beginner, intermediate, expert
    
    # Capital and Risk Control
    total_capital = Column(Float, default=100000.0)  # INR/USDT base capital
    risk_per_trade_percent = Column(Float, default=1.0)  # default 1% risk per trade
    max_daily_loss_percent = Column(Float, default=3.0)  # max daily loss circuit breaker
    max_active_positions = Column(Integer, default=3)
    
    # Behavioral state tracker (Dynamic stats from Layer 2 / Layer 10 psychological check)
    consecutive_losses = Column(Integer, default=0)
    emotional_flags = Column(JSON, default=dict)  # {"fomo": False, "panic": False, "revenge": False}
    adjusted_confidence_threshold = Column(Float, default=62.0)  # Dynamic threshold base
    
    # API credentials for individual brokers (stored encrypted in prod, plain for local dev/testing)
    broker_credentials = Column(JSON, default=dict)  # {"broker": "mock", "api_key": "...", ...}
    
    # Autonomous trading session controls
    trading_session_active = Column(Boolean, default=False)
    trading_session_end = Column(DateTime(timezone=True), nullable=True)

