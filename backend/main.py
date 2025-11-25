from fastapi import FastAPI, Depends, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List, Optional
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio

from services.signal_service import generate_signal_service as generate_signal
from database import get_db, save_signal, get_signal_history, Signal
from config import settings
from logger import logger

# Initialize FastAPI with metadata
app = FastAPI(
    title="Crypto AI Backend",
    description="API pour signaux de trading crypto avec Machine Learning",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Prometheus monitoring
Instrumentator().instrument(app).expose(app)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Restricted to frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "detail": "Une erreur interne s'est produite"
        }
    )

# Pydantic models with validation
class RequestData(BaseModel):
    symbol: str
    timeframe: str = "1h"
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if v not in settings.default_cryptos:
            raise ValueError(f"Symbol must be one of {settings.default_cryptos}")
        return v
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        if v not in settings.available_timeframes:
            raise ValueError(f"Timeframe must be one of {settings.available_timeframes}")
        return v

class MultiRequestData(BaseModel):
    symbols: List[str]
    timeframe: str = "1h"
    
    @validator('symbols')
    def validate_symbols(cls, v):
        for symbol in v:
            if symbol not in settings.default_cryptos:
                raise ValueError(f"All symbols must be in {settings.default_cryptos}")
        return v
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        if v not in settings.available_timeframes:
            raise ValueError(f"Timeframe must be one of {settings.available_timeframes}")
        return v

@app.get("/", tags=["Health"])
def read_root():
    """Root endpoint - System status"""
    return {
        "status": "System Operational",
        "service": "Crypto AI Backend",
        "version": "2.0.0"
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "now"}

@app.get("/cryptos/list", tags=["Configuration"])
def get_crypto_list():
    """
    Get list of supported cryptocurrencies and timeframes
    
    Returns:
        dict: Available cryptos and timeframes
    """
    return {
        "cryptos": settings.default_cryptos,
        "timeframes": settings.available_timeframes
    }

class SettingsUpdate(BaseModel):
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    default_crypto: Optional[str] = None
    default_timeframe: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    alerts_enabled: Optional[bool] = None

@app.get("/settings", tags=["Configuration"])
def get_settings_api():
    """Get current settings"""
    from database import get_settings_from_db
    db_settings = get_settings_from_db()
    
    # Merge with defaults/env if not in DB
    return {
        "binanceApiKey": db_settings.get("binance_api_key", settings.binance_api_key),
        "binanceSecretKey": db_settings.get("binance_secret_key", settings.binance_secret_key),
        "defaultCrypto": db_settings.get("default_crypto", settings.default_cryptos[0]),
        "defaultTimeframe": db_settings.get("default_timeframe", settings.default_timeframe),
        "telegramBotToken": db_settings.get("telegram_bot_token", settings.telegram_bot_token),
        "telegramChatId": db_settings.get("telegram_chat_id", settings.telegram_chat_id),
        "alertsEnabled": db_settings.get("alerts_enabled", "true") == "true"
    }

@app.post("/settings", tags=["Configuration"])
def update_settings_api(data: SettingsUpdate):
    """Update settings"""
    from database import update_setting
    
    if data.binance_api_key is not None: update_setting("binance_api_key", data.binance_api_key)
    if data.binance_secret_key is not None: update_setting("binance_secret_key", data.binance_secret_key)
    if data.default_crypto is not None: update_setting("default_crypto", data.default_crypto)
    if data.default_timeframe is not None: update_setting("default_timeframe", data.default_timeframe)
    if data.telegram_bot_token is not None: update_setting("telegram_bot_token", data.telegram_bot_token)
    if data.telegram_chat_id is not None: update_setting("telegram_chat_id", data.telegram_chat_id)
    if data.alerts_enabled is not None: update_setting("alerts_enabled", str(data.alerts_enabled).lower())
    
    return {"status": "updated"}

@app.post("/backtest", tags=["Analysis"])
@limiter.limit("2/minute")
async def run_backtest(request: Request, symbol: str = "BTCUSDT", days: int = 30):
    """
    Run backtest simulation for a symbol
    
    Args:
        symbol: Crypto symbol to backtest
        days: Number of days to simulate (default: 30)
        
    Returns:
        dict: Backtest results with profit, win rate, trades
        
    Example:
        GET /backtest?symbol=BTCUSDT&days=30
    """
    try:
        from ml.backtest import simulate_trading
        
        if days > 90:
            raise HTTPException(status_code=400, detail="Maximum 90 days allowed")
        
        results = simulate_trading(symbol, days)
        return results
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-signal", tags=["Signals"])
@limiter.limit("10/minute")
async def get_signal(request: Request, data: RequestData):
    """
    Get trading signal for a single cryptocurrency
    
    Args:
        data: RequestData with symbol and timeframe
        
    Returns:
        dict: Signal data with indicators and chart data
        
    Example:
        ```json
        {
            "symbol": "BTCUSDT",
            "timeframe": "1h"
        }
        ```
    """
    try:
        signal_data = generate_signal(data.symbol, data.timeframe)
        
        if "error" not in signal_data:
            save_signal(signal_data)
        
        return signal_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signals/multi", tags=["Signals"])
@limiter.limit("5/minute")
async def get_multi_signals(request: Request, data: MultiRequestData):
    """
    Get signals for multiple cryptocurrencies
    
    Args:
        data: MultiRequestData with list of symbols and timeframe
        
    Returns:
        dict: List of signals for each cryptocurrency
    """
    try:
        results = []
        for symbol in data.symbols:
            signal_data = generate_signal(symbol, data.timeframe)
            if "error" not in signal_data:
                save_signal(signal_data)
            results.append(signal_data)
        return {"signals": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals/history", tags=["Signals"])
@limiter.limit("20/minute")
async def get_history(request: Request, symbol: Optional[str] = None, limit: int = 100):
    """
    Get signal history from database
    
    Args:
        symbol: Optional crypto symbol to filter
        limit: Maximum number of results (default: 100)
        
    Returns:
        dict: Historical signals with metadata
    """
    try:
        if limit > 1000:
            raise HTTPException(status_code=400, detail="Limit cannot exceed 1000")
            
        signals = get_signal_history(symbol, limit)
        return {
            "count": len(signals),
            "signals": [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "timeframe": s.timeframe,
                    "signal": s.signal,
                    "confidence": s.confidence,
                    "price": s.price,
                    "indicators": {
                        "rsi": s.rsi,
                        "ema20": s.ema20,
                        "ema50": s.ema50,
                        "macd": s.macd
                    },
                    "timestamp": s.timestamp.isoformat() + "Z"
                }
                for s in signals
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """
    WebSocket endpoint for real-time signal updates
    
    Sends signal updates every 30 seconds for all default cryptos
    """
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        while True:
            # Generate signals for all default cryptos
            signals = []
            for symbol in settings.default_cryptos:
                try:
                    signal_data = generate_signal(symbol, "1h")
                    if "error" not in signal_data:
                        signals.append(signal_data)
                except Exception as e:
                    logger.error(f"Error generating signal for {symbol}: {e}")
            
            # Send to client
            await websocket.send_json({
                "type": "signals_update",
                "data": signals,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # Wait 30 seconds before next update
            await asyncio.sleep(30)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
