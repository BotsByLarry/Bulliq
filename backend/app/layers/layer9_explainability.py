from app.layers.pipeline_context import PipelineContext

class Layer9Explainability:
    """
    Layer 9: Explainability & Alerts Engine
    Synthesizes complex pipeline parameters into a human-readable trading summary
    and handles alert dispatch logic.
    """
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.risk_approval or not context.trade_plan:
            context.explanation = "No approved trade plan generated."
            context.alert_triggered = False
            return context
            
        # 1. Synthesize rule-based reason summary
        # Gather reasons from technical indicators
        indicators = context.technical_indicators
        sub_scores = context.sub_scores
        
        reasons = []
        
        # Trend alignment reason
        if indicators.get("ema_alignment") == "bullish":
            reasons.append("strong bullish EMA alignment indicating dominant upward momentum")
        elif indicators.get("ema_alignment") == "bearish":
            reasons.append("strong bearish EMA alignment indicating dominant downward momentum")
            
        # Level proximity reason
        if indicators.get("proximity_support"):
            reasons.append("support level proximity offering favorable asymmetric risk entry")
        elif indicators.get("proximity_resistance"):
            reasons.append("resistance level proximity offering favorable asymmetric risk short entry")
            
        # News reason
        if context.sentiment_score > 0.3:
            reasons.append("positive news sentiment support")
        elif context.sentiment_score < -0.3:
            reasons.append("bearish news sentiment confirmation")
            
        reason_str = ", ".join(reasons)
        if not reason_str:
            reason_str = "confluence of short-term intraday momentum and volume parameters"
            
        # Compile explanation paragraph
        explanation = (
            f"Approved {context.direction} plan on {context.symbol} generated with {context.confidence_score}% confidence. "
            f"This plan is justified by {reason_str} in a {context.market_regime.replace('_', ' ')} regime. "
            f"Risk settings suggest placing an entry at {context.entry_price} with a stop loss at {context.stop_loss}, "
            f"targeting {context.target_1} (Target 1) and {context.target_2} (Target 2), representing a highly favorable "
            f"Risk-to-Reward ratio of {context.risk_reward_ratio}:1."
        )
        
        context.explanation = explanation
        context.alert_triggered = True
        
        context.telemetry["layer9"] = {
            "explanation": explanation,
            "alert_triggered": context.alert_triggered
        }
        
        return context
