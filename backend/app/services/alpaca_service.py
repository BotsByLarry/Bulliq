import requests
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class AlpacaService:
    """
    Handles live connectivity and order execution on Alpaca Paper/Live accounts.
    Natively compiles complex Bracket Orders (with joint entry, stop loss, and take profit targets).
    """
    
    def __init__(self):
        self.base_url = (
            "https://paper-api.alpaca.markets" 
            if settings.ALPACA_PAPER 
            else "https://api.alpaca.markets"
        )
        
    def _get_headers(self) -> Dict[str, str]:
        if not settings.ALPACA_API_KEY or not settings.ALPACA_SECRET_KEY:
            raise ValueError("Alpaca credentials (ALPACA_API_KEY / ALPACA_SECRET_KEY) are unconfigured.")
        return {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json"
        }
        
    def get_account_details(self) -> Dict[str, Any]:
        """Fetches active paper account status, buying power, and portfolio equity."""
        try:
            url = f"{self.base_url}/v2/account"
            res = requests.get(url, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                return res.json()
            else:
                logger.error(f"Alpaca account check failed with code {res.status_code}: {res.text}")
                return {}
        except Exception as e:
            logger.error(f"Error querying Alpaca account details: {str(e)}")
            return {}
            
    def execute_bracket_order(
        self, 
        symbol: str, 
        qty: float, 
        side: str, 
        take_profit_price: float, 
        stop_loss_price: float
    ) -> Dict[str, Any]:
        """
        Submits a native bracket order on Alpaca containing an entry market execution,
        an linked take-profit limit, and an linked stop-loss cover order.
        """
        try:
            url = f"{self.base_url}/v2/orders"
            
            # Format the symbol: Alpaca prefers standard format (e.g. BTC/USD or AAPL)
            # If symbol comes as "CRYPTO:BTCUSDT" or "NSE:RELIANCE", strip prefixes and adapt for US paper markets
            formatted_sym = symbol.split(":")[-1]
            if "USDT" in formatted_sym:
                formatted_sym = formatted_sym.replace("USDT", "/USD") # BTCUSDT -> BTC/USD for Alpaca
                
            payload = {
                "symbol": formatted_sym,
                "qty": str(qty),
                "side": side.lower(),
                "type": "market",
                "time_in_force": "gtc",
                "order_class": "bracket",
                "take_profit": {
                    "limit_price": str(take_profit_price)
                },
                "stop_loss": {
                    "stop_price": str(stop_loss_price)
                }
            }
            
            headers = self._get_headers()
            logger.info(f"Submitting native bracket order to Alpaca: {side} {qty} {formatted_sym} (TP: {take_profit_price}, SL: {stop_loss_price})")
            
            res = requests.post(url, headers=headers, json=payload, timeout=12)
            if res.status_code == 200 or res.status_code == 201:
                order_data = res.json()
                logger.info(f"Alpaca bracket order execution SUCCESS. Order ID: {order_data.get('id')}")
                return order_data
            else:
                logger.error(f"Alpaca order submission failed with code {res.status_code}: {res.text}")
                return {"error": res.text, "status_code": res.status_code}
                
        except Exception as e:
            logger.error(f"Failed to execute Alpaca bracket order: {str(e)}")
            return {"error": str(e)}
