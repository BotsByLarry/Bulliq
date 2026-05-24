import time
from app.layers.pipeline_context import PipelineContext

class Layer10AntiError:
    """
    Layer 10: Anti-Error & Guardrails Framework
    Runs cross-validation checks on price feeds, detects staleness, matches psychological triggers,
    and acts as the final gatekeeper to prevent false positives and human execution errors.
    """
    
    def process(self, context: PipelineContext) -> PipelineContext:
        logs = []
        safe_to_trade = True
        
        # 1. Price feed staleness validation
        time_skew = time.time() - context.timestamp
        if time_skew > 10.0:  # Data older than 10 seconds is stale for day trading!
            safe_to_trade = False
            logs.append(f"Price feed staleness detected (skew of {round(time_skew, 2)}s)")
            
        # 2. Outlier / Spike validation
        if context.ticks:
            latest_tick = context.ticks[-1]
            last_price = latest_tick.get("last_price", 0.0)
            price = latest_tick.get("price", 0.0)
            
            if last_price > 0.0:
                percent_change = abs(price - last_price) / last_price * 100
                if percent_change > 3.0: # Intraday tick spike > 3% is highly suspicious
                    safe_to_trade = False
                    logs.append(f"Suspicious tick price spike detected ({round(percent_change, 2)}% single tick change)")
                    
        # 3. Spread ratio check
        # High spreads indicate low liquidity, which leads to high slippage
        if context.spread_ratio > 3.0:
            safe_to_trade = False
            logs.append(f"Extremely high spread ratio ({context.spread_ratio}) indicates insufficient liquidity")
            
        # 4. Psychological protection override
        # If FOMO flag is raised, we reject trades that trigger far from support/resistance levels
        if context.behavioral_flags.get("fomo", False):
            tech = context.technical_indicators
            if not tech.get("proximity_support") and not tech.get("proximity_resistance"):
                safe_to_trade = False
                logs.append("Trade cancelled by FOMO mitigation guardrail (no nearby key levels to anchor entry)")
                
        # If any guardrail failed, override upstream approvals
        if not safe_to_trade:
            context.safe_to_trade = False
            context.risk_approval = False
            context.trade_plan = None
            context.explanation = "Trade cancelled by Layer 10 Anti-Error guardrails."
            
        context.anti_error_logs = logs
        context.telemetry["layer10"] = {
            "safe_to_trade": safe_to_trade,
            "validation_logs": logs
        }
        
        return context
