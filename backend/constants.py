"""
Backend Constants
Centralized constants for the crypto trading backend
"""

# ============================================
# API & Network
# ============================================
DEFAULT_API_TIMEOUT = 10  # seconds
BINANCE_API_TIMEOUT = 15  # seconds
TELEGRAM_API_TIMEOUT = 10  # seconds

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
RETRY_MIN_WAIT = 1  # seconds
RETRY_MAX_WAIT = 10  # seconds

# ============================================
# WebSocket & Real-time Updates
# ============================================
WEBSOCKET_UPDATE_INTERVAL = 30  # seconds
TELEGRAM_ALERT_CHECK_INTERVAL = 3600  # 1 hour in seconds

# ============================================
# Database
# ============================================
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20
DB_POOL_PRE_PING = True

# Query limits
DEFAULT_QUERY_LIMIT = 100
MAX_QUERY_LIMIT = 1000
DEFAULT_QUERY_OFFSET = 0

# ============================================
# Cache
# ============================================
DEFAULT_CACHE_TTL = 60  # seconds
SENTIMENT_CACHE_TTL = 3600  # 1 hour
MODEL_CACHE_TTL = 86400  # 24 hours

# ============================================
# ML & Predictions
# ============================================
MIN_DATA_POINTS = 50  # Minimum candles needed for prediction
MODEL_LOAD_TIMEOUT = 30  # seconds
PREDICTION_TIMEOUT = 5  # seconds

# Fallback heuristic weights
HEURISTIC_WEIGHT_EMA = 0.3
HEURISTIC_WEIGHT_RSI = 0.25
HEURISTIC_WEIGHT_MACD = 0.25
HEURISTIC_WEIGHT_VOLUME = 0.2

# ============================================
# Rate Limiting
# ============================================
RATE_LIMIT_SIGNAL = "10/minute"
RATE_LIMIT_MULTI_SIGNAL = "5/minute"
RATE_LIMIT_BACKTEST = "2/minute"
RATE_LIMIT_HISTORY = "20/minute"

# Binance API rate limits (per minute)
BINANCE_RATE_LIMIT_WEIGHT = 1200
BINANCE_RATE_LIMIT_ORDERS = 50

# ============================================
# Backtest
# ============================================
DEFAULT_BACKTEST_DAYS = 30
MAX_BACKTEST_DAYS = 90
MIN_BACKTEST_DAYS = 7

# ============================================
# Logging
# ============================================
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================
# Error Messages
# ============================================
ERROR_INSUFFICIENT_DATA = "Insufficient data for analysis"
ERROR_BINANCE_API = "Binance API error"
ERROR_MODEL_NOT_FOUND = "ML model not found"
ERROR_PREDICTION_FAILED = "Prediction failed"
ERROR_INVALID_SYMBOL = "Invalid symbol"
ERROR_INVALID_TIMEFRAME = "Invalid timeframe"
ERROR_DATABASE = "Database error"
ERROR_TELEGRAM = "Telegram notification error"

# ============================================
# Success Messages
# ============================================
SUCCESS_SIGNAL_GENERATED = "Signal generated successfully"
SUCCESS_MODEL_LOADED = "Model loaded successfully"
SUCCESS_SETTINGS_UPDATED = "Settings updated successfully"

# ============================================
# Telegram Bot
# ============================================
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_RETRY_ATTEMPTS = 3
TELEGRAM_RETRY_DELAY = 2  # seconds

# ============================================
# Data Validation
# ============================================
MIN_PRICE = 0.00000001  # Minimum valid price
MAX_PRICE = 1000000000  # Maximum valid price
MIN_VOLUME = 0
MAX_RSI = 100
MIN_RSI = 0

# ============================================
# Signal Emojis
# ============================================
EMOJI_BUY = "🟢"
EMOJI_SELL = "🔴"
EMOJI_NEUTRAL = "⚪"
EMOJI_ALERT = "🚨"
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARNING = "⚠️"
EMOJI_INFO = "ℹ️"
EMOJI_CHART = "📊"
EMOJI_ROCKET = "🚀"
