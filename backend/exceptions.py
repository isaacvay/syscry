"""
Custom Exceptions for Crypto Trading Backend
Provides specific exception types for better error handling and debugging
"""


class CryptoBackendException(Exception):
    """Base exception for all backend errors"""
    pass


# ============================================
# API & External Service Errors
# ============================================

class BinanceAPIError(CryptoBackendException):
    """Raised when Binance API request fails"""
    pass


class TelegramAPIError(CryptoBackendException):
    """Raised when Telegram API request fails"""
    pass


class ExternalAPIError(CryptoBackendException):
    """Raised when external API (Twitter, Reddit, News) fails"""
    pass


# ============================================
# Data Errors
# ============================================

class InsufficientDataError(CryptoBackendException):
    """Raised when not enough data is available for analysis"""
    pass


class DataQualityError(CryptoBackendException):
    """Raised when data quality is poor (NaN, invalid values)"""
    pass


class InvalidSymbolError(CryptoBackendException):
    """Raised when symbol is not supported"""
    pass


class InvalidTimeframeError(CryptoBackendException):
    """Raised when timeframe is not supported"""
    pass


# ============================================
# ML & Model Errors
# ============================================

class ModelNotFoundError(CryptoBackendException):
    """Raised when ML model file is not found"""
    pass


class ModelLoadError(CryptoBackendException):
    """Raised when ML model fails to load"""
    pass


class PredictionError(CryptoBackendException):
    """Raised when prediction fails"""
    pass


class FeatureError(CryptoBackendException):
    """Raised when feature engineering fails"""
    pass


# ============================================
# Database Errors
# ============================================

class DatabaseError(CryptoBackendException):
    """Base class for database errors"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass


class DuplicateSignalError(DatabaseError):
    """Raised when trying to insert duplicate signal"""
    pass


class SettingsNotFoundError(DatabaseError):
    """Raised when settings key is not found"""
    pass


# ============================================
# Configuration Errors
# ============================================

class ConfigurationError(CryptoBackendException):
    """Raised when configuration is invalid or missing"""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing"""
    pass


# ============================================
# Validation Errors
# ============================================

class ValidationError(CryptoBackendException):
    """Raised when input validation fails"""
    pass


class RateLimitError(CryptoBackendException):
    """Raised when rate limit is exceeded"""
    pass
