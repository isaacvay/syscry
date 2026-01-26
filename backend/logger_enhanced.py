"""
Enhanced logging module with structured logging and rotation
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import json
import traceback
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            log_data['stack_trace'] = traceback.format_exception(*record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add performance metrics if present
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration
        
        # Add error context if present
        if hasattr(record, 'error_context'):
            log_data['error_context'] = record.error_context
        
        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output
    """
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class PerformanceLogger:
    """
    Context manager for performance logging
    """
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.debug(f"Starting {self.operation}", **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation} in {duration:.2f}ms")
        else:
            self.logger.error(f"Failed {self.operation} in {duration:.2f}ms: {exc_val}")


def setup_logger(
    name: str = "crypto_ai",
    level: str = "INFO",
    log_file: str = "logs/app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    json_format: bool = False
) -> logging.Logger:
    """
    Setup logger with file rotation and console output
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        json_format: Use JSON format for file logs
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    if json_format:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
    
    logger.addHandler(file_handler)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%H:%M:%S'
    ))
    logger.addHandler(console_handler)
    
    return logger


# Create default logger
logger = setup_logger()


def log_with_context(level: str, message: str, **context):
    """
    Log message with additional context
    
    Args:
        level: Log level
        message: Log message
        **context: Additional context fields
    """
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "(unknown file)",
        0,
        message,
        (),
        None
    )
    record.extra_fields = context
    logger.handle(record)


def log_exception(exception: Exception, context: Optional[Dict[str, Any]] = None, 
                 operation: Optional[str] = None):
    """
    Log exception with full context and stack trace
    
    Args:
        exception: Exception to log
        context: Additional context
        operation: Operation that failed
    """
    error_context = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
    }
    
    if context:
        error_context.update(context)
    
    if hasattr(exception, 'to_dict'):
        error_context.update(exception.to_dict())
    
    message = f"Exception in {operation}: {exception}" if operation else f"Exception: {exception}"
    
    logger.exception(message)


def log_performance_warning(operation: str, duration_ms: float, threshold_ms: float = 5000, **context):
    """
    Log performance warning if operation exceeds threshold
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        threshold_ms: Warning threshold in milliseconds
        **context: Additional context
    """
    if duration_ms > threshold_ms:
        logger.warning(
            f"Performance warning: {operation} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)"
        )


def log_api_call(method: str, url: str, status_code: Optional[int] = None, 
                duration_ms: Optional[float] = None, **context):
    """
    Log API call with standardized format
    
    Args:
        method: HTTP method
        url: API URL
        status_code: Response status code
        duration_ms: Request duration
        **context: Additional context
    """
    message = f"{method} {url}"
    
    log_context = {
        "api_method": method,
        "api_url": url,
        **context
    }
    
    if status_code:
        message += f" -> {status_code}"
        log_context["status_code"] = status_code
    
    if duration_ms:
        message += f" ({duration_ms:.2f}ms)"
        log_context["duration_ms"] = duration_ms
    
    if status_code and status_code >= 400:
        logger.error(message)
    elif duration_ms and duration_ms > 5000:
        logger.warning(message)
    else:
        logger.info(message)


# Convenience functions
def debug(message: str, **context):
    """Log debug message with context"""
    log_with_context('DEBUG', message, **context)


def info(message: str, **context):
    """Log info message with context"""
    log_with_context('INFO', message, **context)


def warning(message: str, **context):
    """Log warning message with context"""
    log_with_context('WARNING', message, **context)


def error(message: str, **context):
    """Log error message with context"""
    log_with_context('ERROR', message, **context)


def critical(message: str, **context):
    """Log critical message with context"""
    log_with_context('CRITICAL', message, **context)


# Performance logging context manager
def performance_log(operation: str, **context):
    """
    Context manager for performance logging
    
    Usage:
        with performance_log("signal_generation", symbol="BTCUSDT"):
            # Your code here
            pass
    """
    return PerformanceLogger(logger, operation, **context)
