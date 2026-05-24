import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.layers.layer1_market_intake import Layer1MarketIntake
from app.layers.layer2_trader_profile import Layer2TraderProfile
from app.layers.layer3_regime_detection import Layer3RegimeDetection
from app.layers.layer4_technical_analysis import Layer4TechnicalAnalysis
from app.layers.layer5_sentiment_engine import Layer5SentimentEngine
from app.layers.layer6_signal_scoring import Layer6SignalScoring
from app.layers.layer7_risk_management import Layer7RiskManagement
from app.layers.layer8_trade_plan import Layer8TradePlan
from app.layers.layer9_explainability import Layer9Explainability
from app.layers.layer10_anti_error import Layer10AntiError
from app.services.alpaca_service import AlpacaService

from app.models.user import User
from app.models.signal import Signal
from app.models.trade import Trade

logger = logging.getLogger(__name__)

class DayTraderIntelligencePipeline:
    """
    Orchestrates the sequential flow of market ticks through the 10 intelligence layers.
    Also handles sandbox execution and paper trading matches against live ticks.
    """
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        
        # Instantiate the 10 layers
        self.layer1 = Layer1MarketIntake()
        self.layer2 = Layer2TraderProfile()
        self.layer3 = Layer3RegimeDetection()
        self.layer4 = Layer4TechnicalAnalysis()
        self.layer5 = Layer5SentimentEngine()
        self.layer6 = Layer6SignalScoring()
        self.layer7 = Layer7RiskManagement()
        self.layer8 = Layer8TradePlan()
        self.layer9 = Layer9Explainability()
        self.layer10 = Layer10AntiError()
        self.alpaca = AlpacaService()
        
    async def process_tick(self, tick: dict, db: AsyncSession) -> dict:
        """
        Main entry point for every tick incoming to the platform.
        Runs all active multi-user pipelines and monitors active sandbox trades.
        """
        symbol = tick["symbol"]
        current_price = tick["price"]
        
        # 1. First: Monitor and update existing open mock/sandbox trades
        await self._audit_open_trades(symbol, current_price, db)
        
        # 2. Query active users in the system to run personalized advisory pipelines
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
        
        pipeline_results = []
        
        for user in users:
            try:
                # Query active trades count for risk limit checks
                trades_result = await db.execute(
                    select(Trade).where(Trade.user_id == user.id, Trade.status == "open")
                )
                active_trades = trades_result.scalars().all()
                active_count = len(active_trades)
                
                # --- SEQUENTIAL 10-LAYER INTELLIGENCE FLOW ---
                
                # Layer 1: Market Intake & Indicators construction
                context = await self.layer1.process(tick, user.id)
                
                # Layer 2: Load trader risk and emotional thresholds
                user_profile = {
                    "trading_style": user.trading_style,
                    "total_capital": user.total_capital,
                    "risk_per_trade_percent": user.risk_per_trade_percent,
                    "consecutive_losses": user.consecutive_losses,
                    "emotional_flags": user.emotional_flags
                }
                context = await self.layer2.process(context, user_profile)
                
                # Layer 3: Regime Detection
                context = self.layer3.process(context)
                
                # Layer 4: Multi-Timeframe Technical Indicators & Level proximity
                context = self.layer4.process(context)
                
                # Layer 5: Sentiment feed ingestion
                context = self.layer5.process(context, mock_mode=self.mock_mode)
                
                # Layer 6: Signal scoring engine
                context = self.layer6.process(context)
                
                # Layer 7: Risk assessment gate
                context = self.layer7.process(context, active_trades_count=active_count)
                
                # Layer 8: Trade Plan compiler
                context = self.layer8.process(context)
                
                # Layer 9: Explainability summary generator
                context = self.layer9.process(context)
                
                # Layer 10: Final anti-error and sanity guardrails check
                context = self.layer10.process(context)
                
                # --- PIPELINE EVALUATION ---
                
                # If a valid signal made it past all 10 layers, write it to database and execute a mock/sandbox trade
                if context.is_signal and context.safe_to_trade and context.risk_approval:
                    # Write Signal details
                    db_signal = Signal(
                        symbol=context.symbol,
                        market=context.symbol.split(":")[0],
                        direction=context.direction,
                        entry_price=context.entry_price,
                        stop_loss=context.stop_loss,
                        target_1=context.target_1,
                        target_2=context.target_2,
                        risk_reward_ratio=context.risk_reward_ratio,
                        confidence_score=context.confidence_score,
                        market_regime=context.market_regime,
                        explanation=context.explanation,
                        invalidation_conditions=context.invalidation_conditions,
                        layers_telemetry=context.telemetry
                    )
                    db.add(db_signal)
                    await db.flush() # Flush to acquire db_signal.id
                    
                    # Check if Alpaca Credentials are configured
                    is_alpaca_live = False
                    from app.core.config import settings
                    if settings.ALPACA_API_KEY and settings.ALPACA_SECRET_KEY:
                        try:
                            alpaca_order = self.alpaca.execute_bracket_order(
                                symbol=context.symbol,
                                qty=context.position_size,
                                side="buy" if context.direction == "BUY" else "sell",
                                take_profit_price=context.target_1,
                                stop_loss_price=context.stop_loss
                            )
                            if "id" in alpaca_order:
                                is_alpaca_live = True
                                logger.info(f"Successfully executed LIVE Alpaca trade for signal {db_signal.id}!")
                        except Exception as ex:
                            logger.error(f"Failed to submit active Alpaca bracket order: {str(ex)}")

                    # Execute Sandbox Trade
                    db_trade = Trade(
                        user_id=user.id,
                        signal_id=db_signal.id,
                        symbol=context.symbol,
                        direction=context.direction,
                        quantity=context.position_size,
                        entry_price=context.entry_price,
                        stop_loss=context.stop_loss,
                        take_profit=context.target_1, # Using target_1 as main profit exit for simple sandbox matching
                        status="open",
                        is_mock=not is_alpaca_live
                    )
                    db.add(db_trade)
                    await db.commit()
                    
                    logger.info(f"Generated SIGNAL & TRADE: {context.direction} {context.symbol} at {context.entry_price}")
                    
                pipeline_results.append({
                    "user_id": user.id,
                    "symbol": symbol,
                    "is_signal": context.is_signal,
                    "direction": context.direction,
                    "confidence_score": context.confidence_score,
                    "market_regime": context.market_regime,
                    "explanation": context.explanation,
                    "telemetry": context.telemetry
                })
                
            except Exception as e:
                logger.error(f"Error executing pipeline for user {user.id}: {str(e)}", exc_info=True)
                
        return {"symbol": symbol, "price": current_price, "results": pipeline_results}
        
    async def _audit_open_trades(self, symbol: str, price: float, db: AsyncSession):
        """
        Iterates over active trades, checking if incoming tick crosses stop loss or profit target bounds.
        """
        result = await db.execute(
            select(Trade).where(Trade.symbol == symbol, Trade.status == "open")
        )
        open_trades = result.scalars().all()
        
        for trade in open_trades:
            close_trade = False
            exit_reason = None
            pnl = 0.0
            
            if trade.direction == "BUY":
                if price <= trade.stop_loss:
                    close_trade = True
                    exit_reason = "sl"
                    pnl = (trade.stop_loss - trade.entry_price) * trade.quantity
                elif price >= trade.take_profit:
                    close_trade = True
                    exit_reason = "tp1"
                    pnl = (trade.take_profit - trade.entry_price) * trade.quantity
            else: # SELL
                if price >= trade.stop_loss:
                    close_trade = True
                    exit_reason = "sl"
                    pnl = (trade.entry_price - trade.stop_loss) * trade.quantity
                elif price <= trade.take_profit:
                    close_trade = True
                    exit_reason = "tp1"
                    pnl = (trade.entry_price - trade.take_profit) * trade.quantity
                    
            if close_trade:
                trade.status = "closed"
                trade.exit_price = price
                trade.exit_reason = exit_reason
                trade.pnl = round(pnl, 2)
                from datetime import datetime
                trade.closed_at = datetime.utcnow()
                
                # Fetch user to update consecutive loss counter
                user_res = await db.execute(select(User).where(User.id == trade.user_id))
                user = user_res.scalar_one_or_none()
                if user:
                    if exit_reason == "sl":
                        user.consecutive_losses += 1
                        # If consecutively losing, raise revenge flags
                        if user.consecutive_losses >= 3:
                            user.emotional_flags = {**user.emotional_flags, "revenge": True}
                    else:
                        user.consecutive_losses = 0
                        user.emotional_flags = {**user.emotional_flags, "revenge": False}
                        
                db.add(trade)
                if user:
                    db.add(user)
                await db.commit()
                logger.info(f"CLOSED TRADE: {trade.id} for {trade.symbol} at {price} PnL: {trade.pnl} ({exit_reason})")
