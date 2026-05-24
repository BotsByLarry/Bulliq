from app.layers.pipeline_context import PipelineContext

class Layer2TraderProfile:
    """
    Layer 2: Trader Profile Engine
    Enforces user profile risk configurations, tracks emotional flags,
    and dynamically raises confidence thresholds after losses to mitigate revenge trading.
    """
    
    async def process(self, context: PipelineContext, user_profile: dict) -> PipelineContext:
        # Load user profile specs
        context.trader_style = user_profile.get("trading_style", "scalp")
        context.capital = user_profile.get("total_capital", 100000.0)
        
        # Calculate maximum risk per trade
        risk_pct = user_profile.get("risk_per_trade_percent", 1.0)
        context.risk_per_trade = round(context.capital * (risk_pct / 100.0), 2)
        
        # Track emotional and performance flags
        consecutive_losses = user_profile.get("consecutive_losses", 0)
        behavioral_flags = user_profile.get("emotional_flags", {})
        
        # base confidence threshold (default 62%)
        base_threshold = 62.0
        
        # Dynamic penalty scaling to protect capital
        penalty = 0.0
        
        if not behavioral_flags.get("bypass_limits", False):
            # Revenge trading mitigation: increase threshold by 4% per consecutive loss
            if consecutive_losses > 0:
                penalty += min(consecutive_losses * 4.0, 16.0) # Cap penalty at 16%
                
            # Emotional flags penalties
            if behavioral_flags.get("fomo", False):
                penalty += 8.0
            if behavioral_flags.get("panic", False):
                penalty += 10.0
            if behavioral_flags.get("revenge", False):
                penalty += 12.0
            
        context.adjusted_confidence_threshold = base_threshold + penalty
        context.behavioral_flags = behavioral_flags
        
        context.telemetry["layer2"] = {
            "risk_per_trade": context.risk_per_trade,
            "consecutive_losses": consecutive_losses,
            "applied_penalty": penalty,
            "adjusted_confidence_threshold": context.adjusted_confidence_threshold
        }
        
        return context
