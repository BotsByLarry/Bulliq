import asyncio
import random
import time
from typing import Callable, Awaitable, List, Dict
from app.data.base_connector import MarketDataConnector

class MockMarketConnector(MarketDataConnector):
    """
    Simulates real-time market data ticks for Indian markets and Cryptocurrencies.
    Utilizes a geometric random walk with regime-based drift to model live markets.
    """
    
    def __init__(self):
        self.subscribed_symbols: List[str] = []
        self.callbacks: List[Callable[[dict], Awaitable[None]]] = []
        self.running = False
        self._task: asyncio.Task = None
        
        # Base prices and volatility settings for mock assets
        self.asset_states: Dict[str, dict] = {
            "NSE:RELIANCE": {"price": 2450.0, "volatility": 0.0003, "drift": 0.00002, "spread": 0.5},
            "NSE:TCS": {"price": 3820.0, "volatility": 0.00025, "drift": -0.00001, "spread": 0.8},
            "NSE:NIFTY50": {"price": 22400.0, "volatility": 0.00015, "drift": 0.00001, "spread": 1.5},
            "CRYPTO:BTCUSDT": {"price": 67250.0, "volatility": 0.0008, "drift": 0.00005, "spread": 1.0},
            "CRYPTO:ETHUSDT": {"price": 3520.0, "volatility": 0.001, "drift": 0.00003, "spread": 0.15}
        }
        
    async def connect(self) -> bool:
        if self.running:
            return True
        self.running = True
        self._task = asyncio.create_task(self._simulation_loop())
        return True
        
    async def disconnect(self) -> bool:
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        return True
        
    async def subscribe(self, symbols: List[str]) -> bool:
        for sym in symbols:
            if sym not in self.subscribed_symbols:
                self.subscribed_symbols.append(sym)
                # Initialize custom price if not present
                if sym not in self.asset_states:
                    self.asset_states[sym] = {"price": 100.0, "volatility": 0.0005, "drift": 0.0, "spread": 0.1}
        return True
        
    async def unsubscribe(self, symbols: List[str]) -> bool:
        for sym in symbols:
            if sym in self.subscribed_symbols:
                self.subscribed_symbols.remove(sym)
        return True
        
    def on_tick(self, callback: Callable[[dict], Awaitable[None]]):
        self.callbacks.append(callback)
        
    async def _simulation_loop(self):
        while self.running:
            try:
                # Limit loop to subscribed symbols, or use default set if none specified for global feed simulation
                targets = self.subscribed_symbols if self.subscribed_symbols else list(self.asset_states.keys())
                
                for symbol in targets:
                    state = self.asset_states.get(symbol)
                    if not state:
                        continue
                    
                    # 1. Periodically shift the regime drift to simulate trending vs choppy markets
                    if random.random() < 0.05:  # 5% chance per tick to alter trend direction
                        state["drift"] = random.uniform(-0.0002, 0.0002)
                    
                    # 2. Geometric Brownian Motion tick step
                    delta_pct = random.normalvariate(state["drift"], state["volatility"])
                    old_price = state["price"]
                    new_price = round(old_price * (1 + delta_pct), 2)
                    state["price"] = new_price
                    
                    # Generate bid/ask spread
                    ask = round(new_price + (state["spread"] / 2.0), 2)
                    bid = round(new_price - (state["spread"] / 2.0), 2)
                    volume = random.randint(100, 5000)
                    
                    tick = {
                        "symbol": symbol,
                        "timestamp": time.time(),
                        "price": new_price,
                        "bid": bid,
                        "ask": ask,
                        "volume": volume,
                        "last_price": old_price
                    }
                    
                    # Fire callbacks
                    for cb in self.callbacks:
                        try:
                            await cb(tick)
                        except Exception:
                            # Log callback errors gracefully without killing the simulation
                            pass
                            
                # Sleep a short interval (e.g. 1 second) between tick events
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5.0)  # Sleep on unhandled errors before retrying
