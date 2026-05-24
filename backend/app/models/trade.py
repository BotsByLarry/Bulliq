from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    
    status = Column(String, default="open")  # open, closed
    pnl = Column(Float, default=0.0)  # absolute P&L in currency
    exit_reason = Column(String, nullable=True)  # sl, tp1, tp2, manual, time_expiry
    
    is_mock = Column(Boolean, default=True)  # True for sandbox paper trading
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
