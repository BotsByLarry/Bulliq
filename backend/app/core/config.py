from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulliq AI Terminal"
    API_V1_STR: str = "/api/v1"
    
    # Mode selection: Set to True to run with synthetic sandbox market data and local rules (no real broker accounts needed)
    MOCK_MODE: bool = True
    
    # Security / Auth (Using local JWT fallback if Firebase isn't configured yet)
    SECRET_KEY: str = "SUPER_SECRET_DEVELOPMENT_KEY_CHANGE_IN_PRODUCTION_12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Firebase settings (optional placeholders for multi-user cloud scale later)
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None
    
    # Database Configuration (Defaults to local SQLite for zero-setup local dev)
    USE_POSTGRES: bool = False
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "daytrader_db"
    POSTGRES_PORT: str = "5432"
    
    @property
    def DATABASE_URL(self) -> str:
        if self.USE_POSTGRES:
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        # Fallback to local zero-dependency SQLite
        return "sqlite+aiosqlite:///./daytrader.db"

        
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # Broker API Credentials (Placeholders - user will provide later)
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    ALPACA_PAPER: bool = True
    
    ANGEL_ONE_API_KEY: Optional[str] = None
    ANGEL_ONE_CLIENT_ID: Optional[str] = None
    ANGEL_ONE_PASSWORD: Optional[str] = None
    ANGEL_ONE_TOTP_KEY: Optional[str] = None
    
    FYERS_CLIENT_ID: Optional[str] = None
    FYERS_SECRET_KEY: Optional[str] = None
    
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    
    # LLM API Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
