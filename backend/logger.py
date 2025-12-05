"""
Unified logging module - imports from logger_enhanced
This file exists for backward compatibility
"""
from logger_enhanced import logger, setup_logger, log_with_context, debug, info, warning, error, critical

__all__ = ['logger', 'setup_logger', 'log_with_context', 'debug', 'info', 'warning', 'error', 'critical']

