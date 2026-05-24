import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict

from app.core.config import settings
from app.core.database import Base, engine, get_db, AsyncSessionLocal
from app.models.user import User
from app.models.signal import Signal
from app.models.trade import Trade
from app.data.mock_connector import MockMarketConnector
from app.layers.pipeline import DayTraderIntelligencePipeline
from app.services.llm_service import LLMService
from app.services.alpaca_service import AlpacaService
from pydantic import BaseModel

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Active WebSocket connections registry
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Active connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Handle dead connections silently
                pass

ws_manager = ConnectionManager()
market_connector = MockMarketConnector()
pipeline = DayTraderIntelligencePipeline(mock_mode=settings.MOCK_MODE)

async def tick_callback(tick: dict):
    """Callback fired on every live market tick"""
    async with AsyncSessionLocal() as db:
        try:
            # Process tick through the 10-layer decision pipeline
            result = await pipeline.process_tick(tick, db)
            
            # Broadcast the latest tick, indicators, and any triggered signals
            broadcast_payload = {
                "type": "tick",
                "data": {
                    "symbol": tick["symbol"],
                    "price": tick["price"],
                    "timestamp": tick["timestamp"],
                    "bid": tick["bid"],
                    "ask": tick["ask"],
                    "volume": tick["volume"]
                }
            }
            await ws_manager.broadcast(broadcast_payload)
            
            # If a signal was generated during pipeline run, broadcast it specifically
            for res in result.get("results", []):
                if res["is_signal"]:
                    await ws_manager.broadcast({
                        "type": "signal",
                        "data": {
                            "symbol": res["symbol"],
                            "direction": res["direction"],
                            "confidence": res["confidence_score"],
                            "regime": res["market_regime"],
                            "explanation": res["explanation"]
                        }
                    })
        except Exception as e:
            logger.error(f"Error handling incoming tick: {str(e)}", exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP FLOW ---
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed default user for local testing if not existing
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == "test@example.com"))
        if not res.scalar_one_or_none():
            logger.info("Seeding test user profile...")
            # Default password 'testpassword' (hashed trivially for development simplicity)
            test_user = User(
                email="test@example.com",
                hashed_password="hashed_placeholder_for_local_testing",
                trading_style="scalp",
                risk_appetite="medium",
                total_capital=100000.0,
                risk_per_trade_percent=1.0,
                consecutive_losses=0,
                emotional_flags={"fomo": False, "panic": False, "revenge": False}
            )
            db.add(test_user)
            await db.commit()
            
    # Connect and launch real-time market data feed simulation
    logger.info("Starting market data feed simulation...")
    market_connector.on_tick(tick_callback)
    await market_connector.connect()
    
    yield
    # --- SHUTDOWN FLOW ---
    logger.info("Stopping market data feed simulation...")
    await market_connector.disconnect()
    logger.info("FastAPI shut down complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-User 10-Layer AI Investment & Day Trading Advisor System",
    lifespan=lifespan
)

# Enable CORS for standard React client ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # for development convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REST ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "running", "mode": "Mock Sandbox" if settings.MOCK_MODE else "Live Feed"}

@app.get(f"{settings.API_V1_STR}/profile")
async def get_profile(db: AsyncSession = Depends(get_db)):
    # Returns default seeded test user for rapid validation
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")
    return user

@app.post(f"{settings.API_V1_STR}/profile/settings")
async def update_profile_settings(settings_data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    # Update properties
    user.trading_style = settings_data.get("trading_style", user.trading_style)
    user.risk_appetite = settings_data.get("risk_appetite", user.risk_appetite)
    user.total_capital = float(settings_data.get("total_capital", user.total_capital))
    user.risk_per_trade_percent = float(settings_data.get("risk_per_trade_percent", user.risk_per_trade_percent))
    
    # Emotional flags
    flags = settings_data.get("emotional_flags", {})
    user.emotional_flags = {
        "fomo": bool(flags.get("fomo", user.emotional_flags.get("fomo", False))),
        "panic": bool(flags.get("panic", user.emotional_flags.get("panic", False))),
        "revenge": bool(flags.get("revenge", user.emotional_flags.get("revenge", False))),
        "bypass_limits": bool(flags.get("bypass_limits", user.emotional_flags.get("bypass_limits", False)))
    }
    
    # Reset consecutive losses manually if capital/risk changed
    if "reset_losses" in settings_data:
        user.consecutive_losses = 0
        user.emotional_flags["revenge"] = False
        
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --- ALPACA BROKER INTEGRATION ---

alpaca_service = AlpacaService()

@app.post(f"{settings.API_V1_STR}/profile/alpaca")
async def save_alpaca_credentials(keys: dict, db: AsyncSession = Depends(get_db)):
    api_key = keys.get("api_key")
    secret_key = keys.get("secret_key")
    
    if not api_key or not secret_key:
        raise HTTPException(status_code=400, detail="Both api_key and secret_key are required.")
        
    # Temporary settings load to test connection
    old_key = settings.ALPACA_API_KEY
    old_secret = settings.ALPACA_SECRET_KEY
    
    settings.ALPACA_API_KEY = api_key
    settings.ALPACA_SECRET_KEY = secret_key
    
    # Verify connection
    acc = alpaca_service.get_account_details()
    if not acc or "id" not in acc:
        # Revert
        settings.ALPACA_API_KEY = old_key
        settings.ALPACA_SECRET_KEY = old_secret
        raise HTTPException(status_code=400, detail="Invalid Alpaca credentials or unable to establish connection.")
        
    # Save to local .env file
    env_path = "c:\\Users\\coder\\OneDrive\\Documents\\Projects\\! INVESTMENT ADVISOR AI AGENT\\backend\\.env"
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
            
        new_lines = []
        has_api = False
        has_secret = False
        
        for line in lines:
            if line.startswith("ALPACA_API_KEY="):
                new_lines.append(f"ALPACA_API_KEY={api_key}\n")
                has_api = True
            elif line.startswith("ALPACA_SECRET_KEY="):
                new_lines.append(f"ALPACA_SECRET_KEY={secret_key}\n")
                has_secret = True
            else:
                new_lines.append(line)
                
        if not has_api:
            new_lines.append(f"ALPACA_API_KEY={api_key}\n")
        if not has_secret:
            new_lines.append(f"ALPACA_SECRET_KEY={secret_key}\n")
            
        with open(env_path, "w") as f:
            f.writelines(new_lines)
            
    except Exception as e:
        logger.error(f"Failed to persist Alpaca keys to .env: {str(e)}")
        
    # Update relational profile details
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()
    if user:
        user.broker_credentials = {
            **user.broker_credentials,
            "broker": "alpaca",
            "api_key": api_key,
            "secret_key": secret_key
        }
        db.add(user)
        await db.commit()
        
    return {"status": "success", "account": acc}

@app.get(f"{settings.API_V1_STR}/signals")
async def get_signals(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Signal).order_by(Signal.created_at.desc()).limit(limit))
    return result.scalars().all()

@app.get(f"{settings.API_V1_STR}/trades")
async def get_trades(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).order_by(Trade.created_at.desc()).limit(limit))
    return result.scalars().all()

@app.get(f"{settings.API_V1_STR}/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Calculate stats
    trades_res = await db.execute(select(Trade))
    trades = trades_res.scalars().all()
    
    total = len(trades)
    closed = [t for t in trades if t.status == "closed"]
    wins = [t for t in closed if t.pnl > 0]
    losses = [t for t in closed if t.pnl <= 0]
    
    win_rate = (len(wins) / len(closed) * 100) if closed else 0.0
    total_pnl = sum(t.pnl for t in closed)
    
    # Active pipeline regime summary telemetry
    signals_res = await db.execute(select(Signal).order_by(Signal.created_at.desc()).limit(1))
    latest_sig = signals_res.scalar_one_or_none()
    current_regime = latest_sig.market_regime if latest_sig else "choppy"
    
    return {
        "total_trades": total,
        "closed_trades": len(closed),
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "current_regime": current_regime,
        "active_warnings": {
            "revenge_trading": any(t.exit_reason == "sl" for t in closed[-3:]) if len(closed) >= 3 else False
        }
    }

# --- CHAT AGENT SERVICE ---

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

llm_service = LLMService()

@app.post(f"{settings.API_V1_STR}/chat")
async def chat_with_agent(chat_req: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()
    
    user_context = ""
    if user:
        user_context = (
            f"User Profile Settings:\n"
            f"- Trading Style: {user.trading_style}\n"
            f"- Risk Appetite: {user.risk_appetite}\n"
            f"- Capital: {user.total_capital}\n"
            f"- Risk Per Trade: {user.risk_per_trade_percent}%\n"
            f"- Consecutive Losses: {user.consecutive_losses}\n"
            f"- Emotional Traps Active: {user.emotional_flags}\n\n"
        )
        
    system_prompt = (
        "You are Bulliq AI, a premium agentic day trading co-pilot for Indian markets (NSE/BSE) and cryptocurrencies.\n"
        "Your first and primary mission is to interactively onboard the user by asking questions to determine their risk profile:\n"
        "1. Active trading capital (e.g. INR or USDT)\n"
        "2. Intraday style (scalping, day trading, or swing trading)\n"
        "3. Allowed risk per trade (e.g. 1% or 2%)\n"
        "4. Past emotional traps they fall into (FOMO, revenge trading, panic selling)\n\n"
        "CRITICAL BEHAVIOR:\n"
        "- Adopt a sharp, clean, institutional, supportive financial advisor persona.\n"
        "- If you do not know these details yet, ask for them politely and progressively in your first few turns. Guide them conversationally rather than throwing a large questionnaire.\n"
        "- Once they disclose this info, summarize their settings, reassure them, and explain that Bulliq is actively running a 10-layer sequential intelligence pipeline on live assets aligning with their settings.\n"
        "- If the user asks for trading advice, provide precise rule-based confluence analysis based on standard EMAs, VWAP proximity, and sentiment, warning them never to trade blindly.\n\n"
        f"{user_context}"
        "Begin your greeting by introducing yourself as Bulliq AI, your elite trading co-pilot."
    )
    
    response_text = await llm_service.get_chat_response(chat_req.messages, system_prompt)
    return {"response": response_text}

# --- WEBSOCKET CHANNEL ---

@app.websocket(f"{settings.API_V1_STR}/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Maintain connection alive, listen for any messages from client (if any)
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)
