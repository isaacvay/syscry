"""
Enhanced Exception Classes for Signal Reliability
Provides detailed error information and structured error handling
"""

import time
from typing import Optional, Dict, Any


class CryptoBackendException(Exception):
    """Base exception for all backend errors with enhanced context"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.original_error = original_error
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "timestamp": self.timestamp,
            "original_error": str(self.original_error) if self.original_error else None
        }


# ============================================
# Circuit Breaker for API Calls
# ============================================

class CircuitBreakerOpenError(CryptoBackendException):
    """Raised when circuit breaker is open"""
    
    def __init__(self, service: str, failure_count: int, timeout: int):
        message = f"Circuit breaker open for {service}. Failures: {failure_count}, Timeout: {timeout}s"
        super().__init__(message, "CIRCUIT_BREAKER_OPEN", {"service": service, "failure_count": failure_count})


class CircuitBreaker:
    """Circuit breaker pattern implementation for API resilience"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.service_name = "unknown"
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError(self.service_name, self.failure_count, self.timeout)
        
        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise
    
    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def reset(self):
        """Reset the circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"


# ============================================
# API & External Service Errors
# ============================================

class BinanceAPIError(CryptoBackendException):
    """Raised when Binance API request fails"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 symbol: Optional[str] = None, attempt: Optional[int] = None):
        context = {}
        if status_code:
            context["status_code"] = status_code
        if symbol:
            context["symbol"] = symbol
        if attempt:
            context["attempt"] = attempt
        
        super().__init__(message, "BINANCE_API_ERROR", context)


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
    
    def __init__(self, message: str, required: Optional[int] = None, 
                 received: Optional[int] = None, symbol: Optional[str] = None):
        context = {}
        if required:
            context["required"] = required
        if received:
            context["received"] = received
        if symbol:
            context["symbol"] = symbol
        
        super().__init__(message, "INSUFFICIENT_DATA", context)


class DataQualityError(CryptoBackendException):
    """Raised when data quality is poor (NaN, invalid values)"""
    
    def __init__(self, message: str, symbol: Optional[str] = None, 
                 quality_issues: Optional[Dict] = None):
        context = {"symbol": symbol} if symbol else {}
        if quality_issues:
            context["quality_issues"] = quality_issues
        
        super().__init__(message, "DATA_QUALITY_ERROR", context)


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
    
    def __init__(self, message: str, model_path: Optional[str] = None, 
                 symbol: Optional[str] = None, timeframe: Optional[str] = None):
        context = {}
        if model_path:
            context["model_path"] = model_path
        if symbol:
            context["symbol"] = symbol
        if timeframe:
            context["timeframe"] = timeframe
        
        super().__init__(message, "MODEL_NOT_FOUND", context)


class ModelLoadError(CryptoBackendException):
    """Raised when ML model fails to load"""
    pass


class PredictionError(CryptoBackendException):
    """Raised when prediction fails"""
    
    def __init__(self, message: str, symbol: Optional[str] = None, 
                 prediction_type: Optional[str] = None, original_error: Optional[Exception] = None):
        context = {}
        if symbol:
            context["symbol"] = symbol
        if prediction_type:
            context["prediction_type"] = prediction_type
        
        super().__init__(message, "PREDICTION_ERROR", context, original_error)


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
    
    def __init__(self, message: str, parameter: Optional[str] = None, 
                 expected_type: Optional[str] = None, received_value: Optional[Any] = None):
        context = {}
        if parameter:
            context["parameter"] = parameter
        if expected_type:
            context["expected_type"] = expected_type
        if received_value is not None:
            context["received_value"] = str(received_value)
        
        super().__init__(message, "CONFIGURATION_ERROR", context)


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing"""
    pass


# ============================================
# Validation Errors
# ============================================

class ValidationError(CryptoBackendException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, constraint: Optional[str] = None):
        context = {}
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)
        if constraint:
            context["constraint"] = constraint
        
        super().__init__(message, "VALIDATION_ERROR", context)


class RateLimitError(CryptoBackendException):
    """Raised when rate limit is exceeded"""
    pass
