import numpy as np
import pandas as pd
from typing import Dict, List, Any
from app.layers.pipeline_context import PipelineContext

class Layer4TechnicalAnalysis:
    """
    Layer 4: Multi-Timeframe Technical Analysis
    Extracts signals from EMAs, MACD, RSI, Bollinger Bands, and support/resistance zones.
    Detects classic candlestick triggers (Pin bars, Engulfing bars).
    """
    
    def process(self, context: PipelineContext) -> PipelineContext:
        candles = context.candles_5m
        if len(candles) < 26: # Need enough candles for MACD 26
            return context
            
        closes = np.array([c["close"] for c in candles])
        highs = np.array([c["high"] for c in candles])
        lows = np.array([c["low"] for c in candles])
        opens = np.array([c["open"] for c in candles])
        
        # 1. EMA Alignments
        ema_9 = self._calculate_ema(closes, 9)
        ema_21 = self._calculate_ema(closes, 21)
        ema_50 = self._calculate_ema(closes, 50)
        
        ema_alignment = "neutral"
        if ema_9[-1] > ema_21[-1] > ema_50[-1]:
            ema_alignment = "bullish"
        elif ema_9[-1] < ema_21[-1] < ema_50[-1]:
            ema_alignment = "bearish"
            
        # 2. RSI Calculation
        rsi = self._calculate_rsi(closes, 14)
        current_rsi = rsi[-1]
        
        # 3. MACD Calculation
        macd_line, signal_line, histogram = self._calculate_macd(closes)
        
        # 4. Bollinger Bands Squeeze
        bb_upper, bb_lower, bb_mid = self._calculate_bollinger_bands(closes, 20, 2.0)
        squeeze = (bb_upper[-1] - bb_lower[-1]) / bb_mid[-1] < 0.05
        
        # 5. Candlestick Trigger Patterns (latest completed candle)
        patterns = []
        if len(candles) >= 3:
            pattern = self._detect_patterns(opens[-3:], highs[-3:], lows[-3:], closes[-3:])
            if pattern:
                patterns.append(pattern)
                
        # 6. Map Key Levels (Supports & Resistances based on recent swings)
        support_levels = [round(float(np.min(lows[-20:])), 2)]
        resistance_levels = [round(float(np.max(highs[-20:])), 2)]
        
        # Level proximity check (within 0.15% of any support or resistance)
        current_price = closes[-1]
        proximity_to_support = any(abs(current_price - s) / s < 0.0015 for s in support_levels)
        proximity_to_resistance = any(abs(current_price - r) / r < 0.0015 for r in resistance_levels)
        
        # Build comprehensive technical report
        context.technical_indicators = {
            "ema_alignment": ema_alignment,
            "rsi": round(current_rsi, 2),
            "macd": {
                "macd_line": round(macd_line[-1], 2),
                "signal_line": round(signal_line[-1], 2),
                "histogram": round(histogram[-1], 2)
            },
            "bb_squeeze": bool(squeeze),
            "proximity_support": bool(proximity_to_support),
            "proximity_resistance": bool(proximity_to_resistance)
        }
        
        context.candlestick_patterns = patterns
        context.key_levels = {
            "supports": support_levels,
            "resistances": resistance_levels
        }
        
        context.telemetry["layer4"] = {
            "indicators": context.technical_indicators,
            "patterns": patterns,
            "levels": context.key_levels
        }
        
        return context
        
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values
        
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
                
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)
            
        return rsi
        
    def _calculate_macd(self, prices: np.ndarray) -> tuple:
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        macd_line = ema_12 - ema_26
        signal_line = self._calculate_ema(macd_line, 9)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
        
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int, num_std: float) -> tuple:
        mid_band = pd.Series(prices).rolling(window=period).mean().values
        std_dev = pd.Series(prices).rolling(window=period).std().values
        upper_band = mid_band + (num_std * std_dev)
        lower_band = mid_band - (num_std * std_dev)
        
        # Replace early NaN values with mid band
        upper_band = np.nan_to_num(upper_band, nan=prices[0])
        lower_band = np.nan_to_num(lower_band, nan=prices[0])
        mid_band = np.nan_to_num(mid_band, nan=prices[0])
        
        return upper_band, lower_band, mid_band
        
    def _detect_patterns(self, opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> dict:
        """Simple pattern matcher for latest completed bar"""
        # Let's inspect the last completed candle (index -2 since index -1 is current active building candle)
        o, h, l, c = opens[-2], highs[-2], lows[-2], closes[-2]
        body = abs(c - o)
        candle_range = h - l
        if candle_range == 0:
            return {}
            
        # Doji check
        if body / candle_range < 0.1:
            return {"pattern": "Doji", "direction": "Neutral", "score": 2}
            
        # Hammer (Pin bar) check: long lower wick, small body at the top
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            return {"pattern": "Hammer", "direction": "Bullish", "score": 4}
            
        # Shooting Star check: long upper wick, small body at the bottom
        if upper_wick > body * 2 and lower_wick < body * 0.5:
            return {"pattern": "Shooting Star", "direction": "Bearish", "score": 4}
            
        # Engulfing pattern check (combining candle -3 and candle -2)
        prev_o, prev_c = opens[-3], closes[-3]
        prev_body = abs(prev_c - prev_o)
        
        if c > o and prev_c < prev_o and c > prev_o and o < prev_c:
            return {"pattern": "Bullish Engulfing", "direction": "Bullish", "score": 5}
        if c < o and prev_c > prev_o and c < prev_o and o > prev_c:
            return {"pattern": "Bearish Engulfing", "direction": "Bearish", "score": 5}
            
        return {}
