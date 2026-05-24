import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from app.layers.pipeline_context import PipelineContext

class Layer1MarketIntake:
    """
    Layer 1: Real-Time Market Intake
    Ingests live tick streams, builds multi-tf OHLC candles, and calculates rolling indicators (VWAP, ATR, momentum).
    """
    
    def __init__(self):
        # In-memory store for raw ticks and candles per symbol
        self.tick_store: Dict[str, List[dict]] = {}
        self.candle_store_5m: Dict[str, List[dict]] = {}
        self.candle_store_15m: Dict[str, List[dict]] = {}
        
    async def process(self, tick: dict, user_id: int) -> PipelineContext:
        symbol = tick["symbol"]
        
        # Initialize store lists
        if symbol not in self.tick_store:
            self.tick_store[symbol] = []
            self.candle_store_5m[symbol] = []
            self.candle_store_15m[symbol] = []
            
        # Store tick
        self.tick_store[symbol].append(tick)
        # Limit tick history to last 1000 ticks to conserve memory
        if len(self.tick_store[symbol]) > 1000:
            self.tick_store[symbol].pop(0)
            
        # Aggregate candles from tick history
        self._aggregate_candles(symbol)
        
        # Calculate VWAP
        vwap = self._calculate_vwap(symbol)
        
        # Calculate ATR
        atr = self._calculate_atr(symbol)
        
        # Create pipeline context
        context = PipelineContext(
            symbol=symbol,
            timestamp=time.time(),
            ticks=self.tick_store[symbol][-10:], # last 10 ticks for telemetry
            candles_5m=self.candle_store_5m[symbol][-20:], # last 20 candles
            candles_15m=self.candle_store_15m[symbol][-20:],
            vwap=vwap,
            atr=atr,
            user_id=user_id
        )
        
        context.telemetry["layer1"] = {
            "ticks_count": len(self.tick_store[symbol]),
            "candles_5m_count": len(self.candle_store_5m[symbol]),
            "calculated_vwap": vwap,
            "calculated_atr": atr
        }
        
        return context
        
    def _aggregate_candles(self, symbol: str):
        ticks = self.tick_store[symbol]
        if not ticks:
            return
            
        # Standardize ticks into 5-minute and 15-minute intervals
        df = pd.DataFrame(ticks)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('datetime', inplace=True)
        
        # Resample to 5m and 15m
        for tf, store in [("5min", self.candle_store_5m[symbol]), ("15min", self.candle_store_15m[symbol])]:
            ohlc = df['price'].resample(tf).ohlc()
            volume = df['volume'].resample(tf).sum()
            
            # Rebuild list
            store.clear()
            for timestamp, row in ohlc.iterrows():
                if pd.isna(row['open']):
                    continue
                store.append({
                    "time": timestamp.timestamp(),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": int(volume.loc[timestamp]) if timestamp in volume else 0
                })
                
    def _calculate_vwap(self, symbol: str) -> float:
        ticks = self.tick_store[symbol]
        if not ticks:
            return 0.0
            
        # VWAP = Sum(Price * Volume) / Sum(Volume)
        total_pv = sum(t["price"] * t["volume"] for t in ticks)
        total_v = sum(t["volume"] for t in ticks)
        
        return round(total_pv / total_v, 2) if total_v > 0 else ticks[-1]["price"]
        
    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        candles = self.candle_store_5m[symbol]
        if len(candles) < period + 1:
            # Fallback to a simple percentage based ATR if not enough candles
            current_price = candles[-1]["close"] if candles else 100.0
            return round(current_price * 0.005, 2)
            
        true_ranges = []
        for i in range(1, len(candles)):
            h = candles[i]["high"]
            l = candles[i]["low"]
            prev_c = candles[i-1]["close"]
            
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            true_ranges.append(tr)
            
        # Calculate moving average of true range (simple moving average for MVP)
        return round(float(np.mean(true_ranges[-period:])), 2)
