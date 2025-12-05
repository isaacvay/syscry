"""
Custom Prometheus metrics for monitoring
"""
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from logger import logger

# ============================================
# Counters
# ============================================

# Signal generation
signal_requests_total = Counter(
    'signal_requests_total',
    'Total number of signal requests',
    ['symbol', 'timeframe', 'status']
)

# Binance API calls
binance_api_calls_total = Counter(
    'binance_api_calls_total',
    'Total number of Binance API calls',
    ['endpoint', 'status']
)

# ML predictions
ml_predictions_total = Counter(
    'ml_predictions_total',
    'Total number of ML predictions',
    ['symbol', 'model_type', 'fallback']
)

# Database operations
db_operations_total = Counter(
    'db_operations_total',
    'Total number of database operations',
    ['operation', 'status']
)

# Telegram notifications
telegram_notifications_total = Counter(
    'telegram_notifications_total',
    'Total number of Telegram notifications sent',
    ['type', 'status']
)

# ============================================
# Histograms (for latency tracking)
# ============================================

# Signal generation latency
signal_generation_duration = Histogram(
    'signal_generation_duration_seconds',
    'Time spent generating signals',
    ['symbol', 'timeframe'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# Binance API latency
binance_api_duration = Histogram(
    'binance_api_duration_seconds',
    'Time spent calling Binance API',
    ['endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

# ML prediction latency
ml_prediction_duration = Histogram(
    'ml_prediction_duration_seconds',
    'Time spent on ML predictions',
    ['symbol', 'model_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0)
)

# Database query latency
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Time spent on database queries',
    ['operation'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# ============================================
# Gauges (for current state)
# ============================================

# ML models loaded
ml_models_loaded = Gauge(
    'ml_models_loaded',
    'Number of ML models currently loaded in cache'
)

# Cache entries
cache_entries = Gauge(
    'cache_entries',
    'Number of entries in cache'
)

# Active WebSocket connections
websocket_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections'
)

# ============================================
# Decorator for automatic metrics
# ============================================

def track_signal_generation(func):
    """Decorator to track signal generation metrics"""
    @wraps(func)
    def wrapper(symbol, timeframe, *args, **kwargs):
        start_time = time.time()
        status = "success"
        
        try:
            result = func(symbol, timeframe, *args, **kwargs)
            
            # Check if error in result
            if isinstance(result, dict) and "error" in result:
                status = "error"
            
            return result
        except Exception as e:
            status = "exception"
            raise
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            signal_requests_total.labels(
                symbol=symbol,
                timeframe=timeframe,
                status=status
            ).inc()
            
            signal_generation_duration.labels(
                symbol=symbol,
                timeframe=timeframe
            ).observe(duration)
            
            logger.debug(f"Signal generation for {symbol} {timeframe}: {duration:.3f}s ({status})")
    
    return wrapper


def track_binance_call(endpoint):
    """Decorator to track Binance API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                binance_api_calls_total.labels(
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                binance_api_duration.labels(
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator


def track_ml_prediction(func):
    """Decorator to track ML prediction metrics"""
    @wraps(func)
    def wrapper(df, symbol="BTCUSDT", interval="1h", *args, **kwargs):
        start_time = time.time()
        model_type = "ensemble" if kwargs.get('use_ensemble', True) else "single"
        fallback = "false"
        
        try:
            result = func(df, symbol, interval, *args, **kwargs)
            return result
        except Exception as e:
            fallback = "true"
            raise
        finally:
            duration = time.time() - start_time
            
            ml_predictions_total.labels(
                symbol=symbol,
                model_type=model_type,
                fallback=fallback
            ).inc()
            
            ml_prediction_duration.labels(
                symbol=symbol,
                model_type=model_type
            ).observe(duration)
    
    return wrapper


def track_db_operation(operation):
    """Decorator to track database operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                db_operations_total.labels(
                    operation=operation,
                    status=status
                ).inc()
                
                db_query_duration.labels(
                    operation=operation
                ).observe(duration)
        
        return wrapper
    return decorator


# ============================================
# Helper functions
# ============================================

def update_ml_models_gauge(count: int):
    """Update the ML models loaded gauge"""
    ml_models_loaded.set(count)


def update_cache_gauge(count: int):
    """Update the cache entries gauge"""
    cache_entries.set(count)


def increment_websocket_connections():
    """Increment WebSocket connections"""
    websocket_connections.inc()


def decrement_websocket_connections():
    """Decrement WebSocket connections"""
    websocket_connections.dec()


def record_telegram_notification(notification_type: str, success: bool):
    """Record a Telegram notification"""
    status = "success" if success else "error"
    telegram_notifications_total.labels(
        type=notification_type,
        status=status
    ).inc()
