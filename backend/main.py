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
import time
from datetime import datetime

from services.signal_service import generate_signal_service as generate_signal
from database import get_db, save_signal, get_signal_history, Signal
from config import settings
from logger_enhanced import logger, log_exception, log_api_call, performance_log
from dependency_manager import dependency_manager

# Import custom metrics
try:
    from metrics import (
        signal_requests_total, ml_models_loaded,
        increment_websocket_connections, decrement_websocket_connections,
        update_ml_models_gauge
    )
    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("Custom metrics not available")
    METRICS_AVAILABLE = False

# Import constants and exceptions with enhanced error handling
try:
    from constants import (
        RATE_LIMIT_SIGNAL, RATE_LIMIT_MULTI_SIGNAL, RATE_LIMIT_BACKTEST,
        RATE_LIMIT_HISTORY, DEFAULT_QUERY_LIMIT, MAX_QUERY_LIMIT,
        DEFAULT_BACKTEST_DAYS, MAX_BACKTEST_DAYS, WEBSOCKET_UPDATE_INTERVAL
    )
    from exceptions import (
        BinanceAPIError, InsufficientDataError, DataQualityError,
        ModelNotFoundError, PredictionError, DatabaseError, ConfigurationError
    )
except ImportError:
    # Fallback values
    RATE_LIMIT_SIGNAL = "10/minute"
    RATE_LIMIT_MULTI_SIGNAL = "5/minute"
    RATE_LIMIT_BACKTEST = "2/minute"
    RATE_LIMIT_HISTORY = "20/minute"
    DEFAULT_QUERY_LIMIT = 100
    MAX_QUERY_LIMIT = 1000
    DEFAULT_BACKTEST_DAYS = 30
    MAX_BACKTEST_DAYS = 90
    WEBSOCKET_UPDATE_INTERVAL = 30
    
    class BinanceAPIError(Exception): pass
    class InsufficientDataError(Exception): pass
    class DataQualityError(Exception): pass
    class ModelNotFoundError(Exception): pass
    class PredictionError(Exception): pass
    class DatabaseError(Exception): pass
    class ConfigurationError(Exception): pass

# Validate configuration and dependencies on startup
try:
    from config_validator import validate_required_settings, print_startup_info
    validate_required_settings()
    print_startup_info()
except ImportError:
    logger.warning("config_validator not found - skipping validation")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    logger.error("Please check your .env file and backend/.env.example")
    raise

# Validate dependencies
dependency_status = dependency_manager.validate_dependencies()
if dependency_status.missing:
    logger.warning(f"Missing optional dependencies: {', '.join(dependency_status.missing)}")
    for dep in dependency_status.missing:
        if dep in ["pandas", "numpy", "ta", "joblib"]:
            logger.error(f"Critical dependency missing: {dep}")
            raise ImportError(f"Critical dependency missing: {dep}")

# Global metrics for monitoring
signal_generation_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "average_response_time": 0.0,
    "last_reset": datetime.utcnow()
}

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

# CORS - Allow frontend URLs (development + production)
# Build dynamic origins list
cors_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "https://syscry-production.up.railway.app",  # Backend (same origin)
]
# Add Railway dynamic frontend URL patterns
if "railway.app" in settings.frontend_url:
    cors_origins.append(settings.frontend_url)
# Also allow any railway.app subdomain for flexibility
cors_origins.append("https://*.up.railway.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Use defined origins list
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# GZIP Compression for responses
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Startup event - Preload ML models
@app.on_event("startup")
async def startup_event():
    """Start services and trigger background model loading"""
    logger.info("Starting up... triggering background tasks")
    
    # Define preloading task
    async def preload_models():
        logger.info("⏳ Starting background model preloading...")
        try:
            from model.predict import load_model
            
            # Preload models for default cryptos and timeframes
            preload_symbols = settings.default_cryptos[:2]  # Preload top 2 to save startup time
            preload_timeframes = ["1h"]  # Most common timeframe
            
            loaded_count = 0
            for symbol in preload_symbols:
                for timeframe in preload_timeframes:
                    try:
                        # Run synchronous load_model in thread pool to avoid blocking event loop
                        model_data = await asyncio.to_thread(
                            load_model, symbol, timeframe, use_ensemble=settings.use_ensemble
                        )
                        if model_data:
                            loaded_count += 1
                            logger.info(f"✅ Preloaded model: {symbol} {timeframe}")
                    except Exception as e:
                        logger.warning(f"Could not preload model for {symbol} {timeframe}: {e}")
            
            logger.info(f"Background preloading complete: {loaded_count} models loaded")
            
            # Update Prometheus gauge
            if METRICS_AVAILABLE:
                update_ml_models_gauge(loaded_count)
                
        except Exception as e:
            logger.error(f"Error during background model preloading: {e}")

    # Launch background task
    asyncio.create_task(preload_models())

    
    # Start background trading service
    try:
        from services.trading_service import trading_service
        trading_service.start()
        logger.info("✅ Background trading service started")
    except Exception as e:
        logger.error(f"Failed to start trading service: {e}")
    
    # Start Telegram alert service
    try:
        from services.telegram_alerts import telegram_alert_service
        telegram_alert_service.start()
        logger.info("✅ Telegram alert service started")
    except Exception as e:
        logger.error(f"Failed to start Telegram alert service: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        from services.trading_service import trading_service
        trading_service.stop()
        logger.info("Trading service stopped")
    except Exception as e:
        logger.error(f"Error stopping trading service: {e}")
    
    try:
        from services.telegram_alerts import telegram_alert_service
        telegram_alert_service.stop()
        logger.info("Telegram alert service stopped")
    except Exception as e:
        logger.error(f"Error stopping Telegram alert service: {e}")

# Enhanced exception handlers with structured logging
@app.exception_handler(BinanceAPIError)
async def binance_error_handler(request: Request, exc: BinanceAPIError):
    log_exception(exc, {"endpoint": str(request.url)}, "Binance API call")
    return JSONResponse(
        status_code=503,
        content={
            "error": "Binance service temporarily unavailable",
            "detail": "Please try again in a few moments",
            "type": "BinanceAPIError",
            "error_code": getattr(exc, 'error_code', None)
        }
    )

@app.exception_handler(InsufficientDataError)
async def insufficient_data_handler(request: Request, exc: InsufficientDataError):
    log_exception(exc, {"endpoint": str(request.url)}, "Data validation")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Insufficient data for analysis",
            "detail": str(exc),
            "type": "InsufficientDataError",
            "context": getattr(exc, 'context', {})
        }
    )

@app.exception_handler(DataQualityError)
async def data_quality_handler(request: Request, exc: DataQualityError):
    log_exception(exc, {"endpoint": str(request.url)}, "Data quality validation")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Data quality issue",
            "detail": str(exc),
            "type": "DataQualityError",
            "context": getattr(exc, 'context', {})
        }
    )

@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    log_exception(exc, {"endpoint": str(request.url)}, "Database operation")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database error",
            "detail": "An error occurred while accessing the database",
            "type": "DatabaseError"
        }
    )

@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    log_exception(exc, {"endpoint": str(request.url)}, "Configuration validation")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Configuration error",
            "detail": str(exc),
            "type": "ConfigurationError",
            "context": getattr(exc, 'context', {})
        }
    )

# Global exception handler (fallback) with enhanced logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_exception(exc, {"endpoint": str(request.url), "method": request.method}, "Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": type(exc).__name__,
            "detail": "An unexpected error occurred"
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
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Enhanced health check - verifies all critical components with dependency status
    
    Returns:
        dict: Comprehensive health status including dependencies and performance metrics
    """
    import requests
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {},
        "dependencies": {},
        "metrics": {}
    }
    
    # Check Database
    try:
        from database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection OK"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        log_exception(e, operation="Health check - Database")
    
    # Check Binance API with timeout
    try:
        start_time = time.time()
        response = requests.get(
            "https://api.binance.com/api/v3/ping",
            timeout=5
        )
        api_duration = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            health_status["components"]["binance_api"] = {
                "status": "healthy",
                "message": "Binance API reachable",
                "response_time_ms": round(api_duration, 2)
            }
        else:
            health_status["status"] = "degraded"
            health_status["components"]["binance_api"] = {
                "status": "degraded",
                "message": f"Binance API returned status {response.status_code}",
                "response_time_ms": round(api_duration, 2)
            }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["binance_api"] = {
            "status": "unhealthy",
            "message": f"Binance API unreachable: {str(e)}"
        }
        log_exception(e, operation="Health check - Binance API")
    
    # Check ML Models
    try:
        from model.predict import _model_cache
        loaded_models = len(_model_cache)
        
        if loaded_models > 0:
            health_status["components"]["ml_models"] = {
                "status": "healthy",
                "message": f"{loaded_models} models loaded in cache",
                "loaded_models": loaded_models,
                "model_list": list(_model_cache.keys())
            }
        else:
            health_status["components"]["ml_models"] = {
                "status": "warning",
                "message": "No models loaded (will load on first request)",
                "loaded_models": 0
            }
    except Exception as e:
        health_status["components"]["ml_models"] = {
            "status": "unknown",
            "message": f"Could not check ML models: {str(e)}"
        }
    
    # Check Cache
    try:
        from cache import cache
        health_status["components"]["cache"] = {
            "status": "healthy",
            "message": "In-memory cache available"
        }
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "message": f"Cache error: {str(e)}"
        }
    
    # Add dependency status
    health_status["dependencies"] = {
        "available": dependency_manager.status.available,
        "missing": dependency_manager.status.missing,
        "features": {
            "sentiment_analysis": dependency_manager.is_feature_available("sentiment_analysis"),
            "ml_prediction": dependency_manager.is_feature_available("ml_prediction"),
            "technical_analysis": dependency_manager.is_feature_available("technical_analysis")
        }
    }
    
    # Add performance metrics
    health_status["metrics"] = {
        "signal_generation": {
            "total_requests": signal_generation_metrics["total_requests"],
            "success_rate": (
                signal_generation_metrics["successful_requests"] / 
                max(signal_generation_metrics["total_requests"], 1)
            ),
            "average_response_time_ms": signal_generation_metrics["average_response_time"],
            "last_reset": signal_generation_metrics["last_reset"].isoformat() + "Z"
        }
    }
    
    return health_status

@app.get("/metrics/summary", tags=["Monitoring"])
async def metrics_summary():
    """
    Get a comprehensive summary of application metrics and performance
    
    Returns:
        dict: Detailed metrics including performance, dependencies, and system status
    """
    try:
        from model.predict import _model_cache
        from cache import cache
        
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - signal_generation_metrics["last_reset"]).total_seconds()
        
        summary = {
            "system": {
                "uptime_seconds": uptime_seconds,
                "uptime_human": f"{uptime_seconds // 3600:.0f}h {(uptime_seconds % 3600) // 60:.0f}m",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "ml_models": {
                "loaded": len(_model_cache),
                "models": list(_model_cache.keys()) if _model_cache else [],
                "cache_size": len(_model_cache)
            },
            "cache": {
                "type": "in-memory",
                "available": True
            },
            "signal_generation": {
                "total_requests": signal_generation_metrics["total_requests"],
                "successful_requests": signal_generation_metrics["successful_requests"],
                "failed_requests": signal_generation_metrics["failed_requests"],
                "success_rate": (
                    signal_generation_metrics["successful_requests"] / 
                    max(signal_generation_metrics["total_requests"], 1)
                ),
                "average_response_time_ms": round(signal_generation_metrics["average_response_time"], 2),
                "requests_per_hour": (
                    signal_generation_metrics["total_requests"] / max(uptime_seconds / 3600, 1/3600)
                )
            },
            "dependencies": {
                "available_count": sum(dependency_manager.status.available.values()),
                "total_count": len(dependency_manager.status.available),
                "missing": dependency_manager.status.missing,
                "features": {
                    "sentiment_analysis": dependency_manager.is_feature_available("sentiment_analysis"),
                    "ml_prediction": dependency_manager.is_feature_available("ml_prediction"),
                    "technical_analysis": dependency_manager.is_feature_available("technical_analysis")
                }
            },
            "configuration": {
                "rsi_thresholds": {
                    "oversold": settings.rsi_oversold,
                    "overbought": settings.rsi_overbought
                },
                "confidence_threshold": settings.confidence_threshold,
                "sentiment_enabled": settings.sentiment_enabled,
                "use_ensemble": settings.use_ensemble
            },
            "endpoints": {
                "prometheus": "/metrics",
                "health_simple": "/health",
                "health_detailed": "/health/detailed",
                "api_docs": "/docs",
                "metrics_summary": "/metrics/summary"
            }
        }
        
        return summary
        
    except Exception as e:
        log_exception(e, operation="Metrics summary generation")
        return {
            "error": "Could not generate metrics summary",
            "detail": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

@app.post("/metrics/reset", tags=["Monitoring"])
async def reset_metrics():
    """
    Reset performance metrics (admin endpoint)
    
    Returns:
        dict: Confirmation of metrics reset
    """
    global signal_generation_metrics
    
    old_metrics = signal_generation_metrics.copy()
    
    signal_generation_metrics = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "average_response_time": 0.0,
        "last_reset": datetime.utcnow()
    }
    
    logger.info("Performance metrics reset", old_metrics=old_metrics)
    
    return {
        "message": "Metrics reset successfully",
        "previous_metrics": old_metrics,
        "reset_time": signal_generation_metrics["last_reset"].isoformat() + "Z"
    }

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
@limiter.limit(RATE_LIMIT_BACKTEST)
async def run_backtest(request: Request, symbol: str = "BTCUSDT", days: int = DEFAULT_BACKTEST_DAYS):
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
        
        if days > MAX_BACKTEST_DAYS:
            raise HTTPException(status_code=400, detail=f"Maximum {MAX_BACKTEST_DAYS} days allowed")
        
        results = simulate_trading(symbol, days)
        return results
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-signal", tags=["Signals"])
@limiter.limit(RATE_LIMIT_SIGNAL)
async def get_signal(request: Request, data: RequestData):
    """
    Get trading signal for a single cryptocurrency with enhanced monitoring
    
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
    start_time = time.time()
    signal_generation_metrics["total_requests"] += 1
    
    try:
        with performance_log("signal_generation", symbol=data.symbol, timeframe=data.timeframe):
            signal_data = generate_signal(data.symbol, data.timeframe)
            
            # Log API call
            duration_ms = (time.time() - start_time) * 1000
            log_api_call("POST", "/get-signal", 200, duration_ms, symbol=data.symbol)
            
            # Update metrics
            signal_generation_metrics["successful_requests"] += 1
            signal_generation_metrics["average_response_time"] = (
                (signal_generation_metrics["average_response_time"] * 
                 (signal_generation_metrics["successful_requests"] - 1) + duration_ms) /
                signal_generation_metrics["successful_requests"]
            )
            
            # Performance warning if too slow
            if duration_ms > 5000:
                logger.warning(
                    f"Slow signal generation: {duration_ms:.2f}ms for {data.symbol}",
                    duration_ms=duration_ms,
                    symbol=data.symbol,
                    timeframe=data.timeframe
                )
            
            if "error" not in signal_data:
                save_signal(signal_data)
            
            return signal_data
            
    except Exception as e:
        signal_generation_metrics["failed_requests"] += 1
        duration_ms = (time.time() - start_time) * 1000
        log_api_call("POST", "/get-signal", 500, duration_ms, symbol=data.symbol, error=str(e))
        log_exception(e, {"symbol": data.symbol, "timeframe": data.timeframe}, "Signal generation")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signals/multi", tags=["Signals"])
@limiter.limit(RATE_LIMIT_MULTI_SIGNAL)
async def get_multi_signals(request: Request, data: MultiRequestData):
    """
    Get signals for multiple cryptocurrencies with enhanced error handling
    
    Args:
        data: MultiRequestData with list of symbols and timeframe
        
    Returns:
        dict: List of signals for each cryptocurrency
    """
    start_time = time.time()
    
    try:
        with performance_log("multi_signal_generation", symbols=data.symbols, timeframe=data.timeframe):
            results = []
            successful_signals = 0
            failed_signals = 0
            
            for symbol in data.symbols:
                try:
                    signal_data = generate_signal(symbol, data.timeframe)
                    if "error" not in signal_data:
                        save_signal(signal_data)
                        successful_signals += 1
                    else:
                        failed_signals += 1
                    results.append(signal_data)
                except Exception as e:
                    failed_signals += 1
                    logger.error(f"Failed to generate signal for {symbol}: {e}")
                    results.append({"symbol": symbol, "error": str(e)})
            
            duration_ms = (time.time() - start_time) * 1000
            log_api_call(
                "POST", "/signals/multi", 200, duration_ms,
                symbols_count=len(data.symbols),
                successful=successful_signals,
                failed=failed_signals
            )
            
            return {
                "signals": results,
                "summary": {
                    "total": len(data.symbols),
                    "successful": successful_signals,
                    "failed": failed_signals
                }
            }
            
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call("POST", "/signals/multi", 500, duration_ms, error=str(e))
        log_exception(e, {"symbols": data.symbols, "timeframe": data.timeframe}, "Multi-signal generation")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals/history", tags=["Signals"])
@limiter.limit(RATE_LIMIT_HISTORY)
async def get_history(
    request: Request, 
    symbol: Optional[str] = None, 
    limit: int = DEFAULT_QUERY_LIMIT,
    offset: int = 0
):
    """
    Get signal history from database with pagination
    
    Args:
        symbol: Optional crypto symbol to filter
        limit: Maximum number of results (default: 100, max: 1000)
        offset: Number of records to skip for pagination (default: 0)
        
    Returns:
        dict: Historical signals with metadata and pagination info
        
    Example:
        GET /signals/history?symbol=BTCUSDT&limit=50&offset=0
    """
    try:
        if limit > MAX_QUERY_LIMIT:
            raise HTTPException(status_code=400, detail=f"Limit cannot exceed {MAX_QUERY_LIMIT}")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset cannot be negative")
            
        signals = get_signal_history(symbol, limit, offset)
        
        return {
            "count": len(signals),
            "limit": limit,
            "offset": offset,
            "has_more": len(signals) == limit,  # Hint if there are more results
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
    
    # Track connection
    if METRICS_AVAILABLE:
        increment_websocket_connections()
    
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
            
            # Wait before next update
            await asyncio.sleep(WEBSOCKET_UPDATE_INTERVAL)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Track disconnection
        if METRICS_AVAILABLE:
            decrement_websocket_connections()
        try:
            await websocket.close()
        except:
            pass


# ============================================
# Trading Session Endpoints
# ============================================

class SessionCreate(BaseModel):
    name: str = "New Session"
    strategyName: str = "Balanced"
    initialBalance: float = 10000.0
    symbols: List[str] = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    strategyConfig: Optional[dict] = None


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    isActive: Optional[bool] = None
    autoTrade: Optional[bool] = None
    strategyName: Optional[str] = None
    strategyRiskPerTrade: Optional[float] = None
    strategyStopLoss: Optional[float] = None
    strategyTakeProfit: Optional[float] = None
    strategyMaxPositions: Optional[int] = None
    strategyTrailingStop: Optional[bool] = None
    symbols: Optional[str] = None


@app.get("/trading/sessions", tags=["Trading Sessions"])
async def list_trading_sessions():
    """
    Get all trading sessions
    
    Returns:
        List of all trading sessions with their current status
    """
    try:
        from services.trading_service import get_all_sessions
        sessions = get_all_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trading/sessions", tags=["Trading Sessions"])
async def create_trading_session(data: SessionCreate):
    """
    Create a new trading session
    
    Args:
        data: Session configuration
        
    Returns:
        Created session details
    """
    try:
        from services.trading_service import create_session
        
        strategy_config = data.strategyConfig or {
            "risk_per_trade": 0.02,
            "stop_loss": 0.03,
            "take_profit": 0.06,
            "max_positions": 5,
            "trailing_stop": True
        }
        
        session = create_session(
            name=data.name,
            strategy_name=data.strategyName,
            initial_balance=data.initialBalance,
            symbols=data.symbols,
            strategy_config=strategy_config
        )
        
        return {"session": session, "message": "Session created successfully"}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/sessions/{session_id}", tags=["Trading Sessions"])
async def get_trading_session(session_id: str):
    """
    Get trading session details including positions and recent trades
    
    Args:
        session_id: Session ID
        
    Returns:
        Session details with positions and trades
    """
    try:
        from services.trading_service import get_session
        session = get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"session": session}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/trading/sessions/{session_id}", tags=["Trading Sessions"])
async def update_trading_session(session_id: str, data: SessionUpdate):
    """
    Update a trading session (start/stop/pause, change settings)
    
    Args:
        session_id: Session ID
        data: Fields to update
        
    Returns:
        Updated session
    """
    try:
        from services.trading_service import update_session
        
        # Convert camelCase to snake_case for database
        updates = {}
        if data.name is not None:
            updates["name"] = data.name
        if data.isActive is not None:
            updates["is_active"] = data.isActive
        if data.autoTrade is not None:
            updates["auto_trade"] = data.autoTrade
        if data.strategyName is not None:
            updates["strategy_name"] = data.strategyName
        if data.strategyRiskPerTrade is not None:
            updates["strategy_risk_per_trade"] = data.strategyRiskPerTrade
        if data.strategyStopLoss is not None:
            updates["strategy_stop_loss"] = data.strategyStopLoss
        if data.strategyTakeProfit is not None:
            updates["strategy_take_profit"] = data.strategyTakeProfit
        if data.strategyMaxPositions is not None:
            updates["strategy_max_positions"] = data.strategyMaxPositions
        if data.strategyTrailingStop is not None:
            updates["strategy_trailing_stop"] = data.strategyTrailingStop
        if data.symbols is not None:
            updates["symbols"] = data.symbols
        
        session = update_session(session_id, updates)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"session": session, "message": "Session updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/trading/sessions/{session_id}", tags=["Trading Sessions"])
async def delete_trading_session(session_id: str):
    """
    Delete a trading session and all related data
    
    Args:
        session_id: Session ID
        
    Returns:
        Deletion confirmation
    """
    try:
        from services.trading_service import delete_session
        success = delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully", "id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trading/sessions/{session_id}/start", tags=["Trading Sessions"])
async def start_trading_session(session_id: str, auto_trade: bool = True):
    """
    Start a trading session
    
    Args:
        session_id: Session ID
        auto_trade: Whether to enable auto-trading
        
    Returns:
        Updated session
    """
    try:
        from services.trading_service import update_session
        session = update_session(session_id, {"is_active": True, "auto_trade": auto_trade})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"session": session, "message": "Session started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trading/sessions/{session_id}/stop", tags=["Trading Sessions"])
async def stop_trading_session(session_id: str):
    """
    Stop a trading session
    
    Args:
        session_id: Session ID
        
    Returns:
        Updated session  
    """
    try:
        from services.trading_service import update_session
        session = update_session(session_id, {"is_active": False, "auto_trade": False})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"session": session, "message": "Session stopped"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

