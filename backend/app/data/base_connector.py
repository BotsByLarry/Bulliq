from abc import ABC, abstractmethod
from typing import Callable, Awaitable, List

class MarketDataConnector(ABC):
    """
    Abstract base class for market data connectors.
    Enables pluggable data sources (e.g. Angel One, Binance, Mock Sandbox).
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Initialize the connection to the feed source."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> bool:
        """Gracefully disconnect from the feed source."""
        pass
        
    @abstractmethod
    async def subscribe(self, symbols: List[str]) -> bool:
        """Subscribe to real-time updates for a list of symbols."""
        pass
        
    @abstractmethod
    async def unsubscribe(self, symbols: List[str]) -> bool:
        """Unsubscribe from real-time updates for a list of symbols."""
        pass
        
    @abstractmethod
    def on_tick(self, callback: Callable[[dict], Awaitable[None]]):
        """Register a callback for handling incoming market ticks."""
        pass
