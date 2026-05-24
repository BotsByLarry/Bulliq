from typing import Dict, Any
from app.layers.pipeline_context import PipelineContext

class Layer8TradePlan:
    """
    Layer 8: Trade Plan Generation
    Constructs the final actionable execution plan outlining entry targets, scaling checkpoints,
    trailing logic, and specific trade invalidation conditions.
    """
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.risk_approval:
            context.trade_plan = None
            return context
            
        # Define trade parameters
        invalidation_conditions = [
            f"Price closes past Stop Loss level of {context.stop_loss}",
            "Time limits: trade fails to trigger or progress within 45 minutes",
            "Regime shifts to choppy/low-liquidity during early consolidation"
        ]
        
        # Build comprehensive actionable plan
        plan = {
            "symbol": context.symbol,
            "direction": context.direction,
            "confidence": f"{context.confidence_score}%",
            "execution": {
                "entry_trigger": f"Market Execution close to {context.entry_price}",
                "position_size": context.position_size,
                "levels": {
                    "stop_loss": context.stop_loss,
                    "target_1": context.target_1,
                    "target_2": context.target_2
                },
                "strategy": {
                    "scale_out": "Sell 50% at Target 1, trail stop to break-even, and exit remainder at Target 2",
                    "trailing_trigger": "Trail SL to entry once price makes 1 ATR excursion in direction of trade"
                }
            },
            "invalidation": invalidation_conditions,
            "regime_context": context.market_regime
        }
        
        context.trade_plan = plan
        context.invalidation_conditions = invalidation_conditions
        
        context.telemetry["layer8"] = {
            "plan_generated": True,
            "plan_details": plan
        }
        
        return context
