import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    binance_api_key: str = ""
    binance_secret_key: str = ""
    
    # Telegram Configuration
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "8182517592:AAES9VxhR5UDjqq2kwfjILH7IH6WN8yLIPw")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "7686161669")
    
    # Trading Configuration
    default_cryptos: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    default_timeframe: str = "1h"
    available_timeframes: List[str] = ["15m", "1h", "4h", "1d", "1w"]
    
    # Cache Configuration
    cache_ttl: int = 60  # seconds
    
    # Signal Thresholds
    rsi_oversold: int = 40
    rsi_overbought: int = 60
    confidence_threshold: float = 0.55
    
    # Database
    database_url: str = "sqlite:///./crypto_signals.db"
    
    # API Settings
    api_rate_limit: int = 100  # requests per minute
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Sentiment Analysis API Keys (Optional)
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "AAAAAAAAAAAAAAAAAAAAAFyU5gEAAAAAqJDLfFYu1KCutNJP0iVXM9WBTDI%3D6E9WgF85PAM5VInPRMno2W0srTKdCD8vxQHEPteDvRBuDByCmM")
    # Reddit API disabled - no access
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = ""
    news_api_key: str = os.getenv("NEWS_API_KEY", "8e8efbc0977f4447963b323cd544e6e3")
    
    # Sentiment Configuration
    sentiment_enabled: bool = True
    sentiment_cache_ttl: int = 3600  # 1 hour
    
    # Hyperparameter Tuning
    enable_hyperparameter_tuning: bool = False
    tuning_method: str = "random"  # grid, random, optuna
    tuning_trials: int = 50
    
    # Ensemble Models
    use_ensemble: bool = True
    ensemble_models: List[str] = ["xgboost", "random_forest", "lightgbm", "catboost"]
    ensemble_type: str = "voting"  # voting, stacking, best
    
    # Leverage & Risk Management
    min_leverage: float = 1.0
    max_leverage: float = 10.0
    default_account_balance: float = 10000.0
    risk_per_trade: float = 0.02  # 2% of capital per trade
    max_portfolio_risk: float = 0.10  # 10% max portfolio risk
    max_drawdown: float = 0.20  # 20% max drawdown
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
