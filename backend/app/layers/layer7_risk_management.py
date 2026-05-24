from app.layers.pipeline_context import PipelineContext

class Layer7RiskManagement:
    """
    Layer 7: Risk Management Engine
    Places precise entry, stop loss, and target levels.
    Enforces risk rules: R:R ratio >= 1.5, position caps, and circuit breakers.
    """
    
    def process(self, context: PipelineContext, active_trades_count: int = 0) -> PipelineContext:
        # If upstream scoring did not trigger a signal, skip risk processing
        if not context.is_signal:
            context.risk_approval = False
            return context
            
        candles = context.candles_5m
        if not candles:
            context.risk_approval = False
            context.risk_rejection_reason = "No market data candles available for risk calculation"
            return context
            
        current_price = candles[-1]["close"]
        atr = context.atr
        direction = context.direction
        
        # 1. Check Circuit Breakers
        if not context.behavioral_flags.get("bypass_limits", False):
            # Max active positions check
            if active_trades_count >= 3:
                context.risk_approval = False
                context.risk_rejection_reason = "Max active positions count reached (3)"
                return context
                
            # Revenge trading lock check
            if context.behavioral_flags.get("revenge", False):
                context.risk_approval = False
                context.risk_rejection_reason = "Trading blocked due to active revenge trading behavioral flag"
                return context
            
        # 2. Place Trade Levels (Entry, SL, Targets)
        # Entry range centered on current price
        entry_price = current_price
        
        # ATR-based stop loss placement (e.g. 1.5 * ATR away)
        atr_multiplier = 1.5
        sl_distance = max(atr * atr_multiplier, current_price * 0.002) # minimum 0.2% stop loss
        
        if direction == "BUY":
            stop_loss = round(entry_price - sl_distance, 2)
            # R:R target 1 (1.5x risk) and target 2 (3x risk)
            target_1 = round(entry_price + (sl_distance * 1.5), 2)
            target_2 = round(entry_price + (sl_distance * 3.0), 2)
        else: # SELL
            stop_loss = round(entry_price + sl_distance, 2)
            target_1 = round(entry_price - (sl_distance * 1.5), 2)
            target_2 = round(entry_price - (sl_distance * 3.0), 2)
            
        # Calculate Risk-Reward Ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(target_1 - entry_price)
        rr_ratio = round(reward / risk, 2) if risk > 0 else 0.0
        
        # 3. Check Risk-Reward gate (Must be >= 1.5:1)
        if rr_ratio < 1.45: # Tolerating floating point variations
            context.risk_approval = False
            context.risk_rejection_reason = f"Risk-Reward ratio {rr_ratio} is below minimum requirement of 1.5:1"
            return context
            
        # 4. Position Sizing
        # formula: quantity = capital_at_risk / sl_distance
        capital_at_risk = context.risk_per_trade
        quantity = round(capital_at_risk / sl_distance, 2) if sl_distance > 0 else 0.0
        
        # Max exposure sanity guard (never use more than 20% of capital for a single position margin)
        max_margin = context.capital * 0.2
        potential_cost = quantity * entry_price
        if potential_cost > max_margin:
            quantity = round(max_margin / entry_price, 2)
            
        # Apply regime modifier (reduce size in choppy, scale up in breakout)
        regime_mod = context.regime_modifiers.get("size_modifier", 1.0)
        quantity = round(quantity * regime_mod, 2)
        
        context.entry_price = entry_price
        context.stop_loss = stop_loss
        context.target_1 = target_1
        context.target_2 = target_2
        context.position_size = quantity
        context.risk_reward_ratio = rr_ratio
        context.risk_approval = True
        
        context.telemetry["layer7"] = {
            "entry": entry_price,
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "position_size": quantity,
            "rr_ratio": rr_ratio,
            "risk_approval": context.risk_approval
        }
        
        return context
