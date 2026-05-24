import numpy as np
from typing import List, Dict
from app.layers.pipeline_context import PipelineContext

class Layer3RegimeDetection:
    """
    Layer 3: Market Regime Detection
    Uses technical indicator alignment, ADX/ATR, and candle slopes to classify the market regime
    (trending, choppy, breakout, low-liquidity) and applies position size modifiers.
    """
    
    def process(self, context: PipelineContext) -> PipelineContext:
        candles = context.candles_5m
        if len(candles) < 20:
            # Fallback for fresh starting systems
            context.market_regime = "choppy"
            context.regime_confidence = 50.0
            return context
            
        closes = np.array([c["close"] for c in candles])
        highs = np.array([c["high"] for c in candles])
        lows = np.array([c["low"] for c in candles])
        volumes = np.array([c["volume"] for c in candles])
        
        # Calculate EMA 9 and 21 slope
        ema_9 = self._calculate_ema(closes, 9)
        ema_21 = self._calculate_ema(closes, 21)
        
        slope_9 = float(ema_9[-1] - ema_9[-3]) / ema_9[-3] * 100 if len(ema_9) > 3 else 0.0
        
        # Calculate ADX (Directional Movement Index)
        adx = self._calculate_adx(highs, lows, closes, 14)
        
        # Check volume growth
        volume_ma_20 = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_expansion = current_volume > (volume_ma_20 * 1.5)
        
        # Regime categorization
        regime = "choppy"
        confidence = 60.0
        size_modifier = 1.0
        
        if adx > 25.0:
            if slope_9 > 0.03:
                regime = "trending_bull"
                confidence = min(50.0 + adx, 100.0)
                size_modifier = 1.0
            elif slope_9 < -0.03:
                regime = "trending_bear"
                confidence = min(50.0 + adx, 100.0)
                size_modifier = 1.0
        elif adx < 18.0:
            regime = "choppy"
            confidence = 80.0
            size_modifier = 0.5 # Reduce size in choppy markets!
        
        # Breakout check (Volume expansion + ADX spike)
        if volume_expansion and adx > 20.0 and abs(slope_9) > 0.05:
            regime = "breakout"
            confidence = 85.0
            size_modifier = 1.2 # Scale up size for clear breakouts!
            
        # VIX sanity check
        if context.vix > 25.0:
            size_modifier = size_modifier * 0.7  # Reduce size by 30% during extremely high macro volatility
            
        context.market_regime = regime
        context.regime_confidence = confidence
        context.regime_modifiers = {
            "size_modifier": round(size_modifier, 2),
            "adx": round(adx, 2),
            "ema_9_slope": round(slope_9, 4),
            "volume_expansion": bool(volume_expansion)
        }
        
        context.telemetry["layer3"] = {
            "regime": regime,
            "regime_confidence": confidence,
            "modifiers": context.regime_modifiers
        }
        
        return context
        
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """EMA calculation using standard pandas/numpy weights"""
        if len(prices) < period:
            return prices
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values
        
    def _calculate_adx(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> float:
        """Calculates Average Directional Index (ADX)"""
        if len(closes) < period * 2:
            return 20.0  # Safe fallback score
            
        up_moves = highs[1:] - highs[:-1]
        down_moves = lows[:-1] - lows[1:]
        
        plus_dm = np.where((up_moves > down_moves) & (up_moves > 0), up_moves, 0.0)
        minus_dm = np.where((down_moves > up_moves) & (down_moves > 0), down_moves, 0.0)
        
        # True Range
        tr = np.zeros(len(closes) - 1)
        for i in range(1, len(closes)):
            h = highs[i]
            l = lows[i]
            prev_c = closes[i-1]
            tr[i-1] = max(h - l, abs(h - prev_c), abs(l - prev_c))
            
        # Smoothings using ewm
        tr_smooth = pd.Series(tr).ewm(alpha=1/period, adjust=False).mean().values
        plus_dm_smooth = pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean().values
        minus_dm_smooth = pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean().values
        
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        # Avoid division by zero
        denom = plus_di + minus_di
        denom = np.where(denom == 0, 1, denom)
        
        dx = 100 * (np.abs(plus_di - minus_di) / denom)
        adx_series = pd.Series(dx).ewm(alpha=1/period, adjust=False).mean().values
        
        return float(adx_series[-1])
