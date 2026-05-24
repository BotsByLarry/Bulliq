from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PipelineContext(BaseModel):
    """
    Context object that flows sequentially through the 10 intelligence layers.
    Maintains telemetry and intermediate state for auditability and reasoning.
    """
    symbol: str
    timestamp: float
    
    # Layer 1: Market Intake Data
    ticks: List[Dict[str, Any]] = Field(default_factory=list)
    candles_5m: List[Dict[str, Any]] = Field(default_factory=list)
    candles_15m: List[Dict[str, Any]] = Field(default_factory=list)
    vwap: float = 0.0
    atr: float = 0.0
    vix: float = 18.0
    spread_ratio: float = 1.0
    
    # Layer 2: Trader Profile
    user_id: int
    trader_style: str = "scalp"
    risk_per_trade: float = 1000.0  # absolute capital at risk
    capital: float = 100000.0
    adjusted_confidence_threshold: float = 62.0
    behavioral_flags: Dict[str, bool] = Field(default_factory=dict)
    
    # Layer 3: Market Regime
    market_regime: str = "choppy"  # trending_bull, trending_bear, choppy, breakout, news_driven
    regime_confidence: float = 50.0
    regime_modifiers: Dict[str, Any] = Field(default_factory=dict)
    
    # Layer 4: Technical Analysis
    technical_indicators: Dict[str, Any] = Field(default_factory=dict) # RSI, MACD, EMA alignments
    candlestick_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    key_levels: Dict[str, Any] = Field(default_factory=dict) # supports, resistances, PDH, PDL
    
    # Layer 5: News & Sentiment
    sentiment_score: float = 0.0  # -1.0 to 1.0
    news_events: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Layer 6: Signal Scoring
    is_signal: bool = False
    direction: Optional[str] = None  # BUY, SELL
    confidence_score: float = 0.0  # 0 to 100
    sub_scores: Dict[str, float] = Field(default_factory=dict) # технічні, об'єм, sentiment
    
    # Layer 7: Risk Management
    entry_price: float = 0.0
    stop_loss: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    position_size: float = 0.0
    risk_reward_ratio: float = 0.0
    risk_approval: bool = False
    risk_rejection_reason: Optional[str] = None
    
    # Layer 8: Trade Plan
    trade_plan: Optional[Dict[str, Any]] = None
    
    # Layer 9: Explainability & Alerts
    explanation: Optional[str] = None
    alert_triggered: bool = False
    
    # Layer 10: Anti-Error & Guardrails
    data_validated: bool = True
    safe_to_trade: bool = True
    anti_error_logs: List[str] = Field(default_factory=list)
    
    # Telemetry logger containing execution metrics for all layers
    telemetry: Dict[str, Any] = Field(default_factory=dict)
