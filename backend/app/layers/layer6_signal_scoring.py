from typing import Dict
from app.layers.pipeline_context import PipelineContext

class Layer6SignalScoring:
    """
    Layer 6: Signal Scoring & Confidence Engine
    Synthesizes technical, volume, sentiment, patterns, and regime indicators into a single score.
    Dynamically adjusts weight biases depending on the current market regime.
    """
    
    def process(self, context: PipelineContext) -> PipelineContext:
        regime = context.market_regime
        indicators = context.technical_indicators
        patterns = context.candlestick_patterns
        
        # 1. Define standard scoring weights
        weights = {
            "technical": 0.28,
            "momentum": 0.20,
            "volume": 0.15,
            "sentiment": 0.12,
            "levels": 0.12,
            "regime_fit": 0.08,
            "pattern": 0.05
        }
        
        # 2. Adjust weights dynamically based on market regime
        if regime == "choppy":
            # In choppy markets, key levels (supports/resistances) hold much higher priority
            weights["levels"] = 0.25
            weights["technical"] = 0.15
        elif regime == "breakout":
            # In breakout environments, volume and momentum hold heavy biases
            weights["volume"] = 0.25
            weights["momentum"] = 0.25
            weights["technical"] = 0.20
            
        # 3. Calculate separate factor scores (0 to 100)
        sub_scores = {}
        
        # Technical Score (EMA alignment, RSI limits)
        tech_score = 50.0
        if indicators.get("ema_alignment") == "bullish":
            tech_score += 25.0
        elif indicators.get("ema_alignment") == "bearish":
            tech_score -= 25.0
        rsi = indicators.get("rsi", 50.0)
        if 40.0 <= rsi <= 60.0:
            tech_score += 15.0
        sub_scores["technical"] = max(0.0, min(100.0, tech_score))
        
        # Momentum Score (MACD histogram directions)
        mom_score = 50.0
        macd = indicators.get("macd", {})
        hist = macd.get("histogram", 0.0)
        if hist > 0:
            mom_score += 30.0
        elif hist < 0:
            mom_score -= 30.0
        sub_scores["momentum"] = max(0.0, min(100.0, mom_score))
        
        # Volume Score
        vol_score = 70.0 if context.regime_modifiers.get("volume_expansion") else 40.0
        sub_scores["volume"] = vol_score
        
        # Sentiment Score (-1.0 to +1.0 converted to 0-100)
        sub_scores["sentiment"] = round((context.sentiment_score + 1.0) * 50.0, 2)
        
        # Levels Score (proximity supports/resistances)
        lvl_score = 50.0
        if indicators.get("proximity_support") or indicators.get("proximity_resistance"):
            lvl_score += 40.0
        sub_scores["levels"] = lvl_score
        
        # Regime Fit Score
        sub_scores["regime_fit"] = context.regime_confidence
        
        # Pattern Score
        pat_score = 50.0
        if patterns:
            pat = patterns[0]
            if pat.get("direction") == "Bullish":
                pat_score += pat.get("score", 0) * 8
            elif pat.get("direction") == "Bearish":
                pat_score -= pat.get("score", 0) * 8
        sub_scores["pattern"] = max(0.0, min(100.0, pat_score))
        
        # 4. Calculate total weighted confidence score
        total_score = sum(sub_scores[k] * weights[k] for k in weights)
        context.confidence_score = round(total_score, 2)
        context.sub_scores = sub_scores
        
        # 5. Determine Signal and Direction
        # Determine direction based on indicators
        direction = "BUY" if sub_scores["technical"] > 50.0 or sub_scores["momentum"] > 50.0 else "SELL"
        context.direction = direction
        
        # Compare with the adjusted confidence threshold from user profile
        is_triggered = context.confidence_score >= context.adjusted_confidence_threshold
        context.is_signal = is_triggered
        
        context.telemetry["layer6"] = {
            "is_signal": context.is_signal,
            "direction": context.direction,
            "confidence_score": context.confidence_score,
            "threshold_required": context.adjusted_confidence_threshold,
            "weights": weights,
            "sub_scores": sub_scores
        }
        
        return context
