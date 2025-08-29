# src/network_rag/infrastructure/logging.py
"""Logging configuration and setup for the network RAG system"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .config import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Setup logging configuration"""
    
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if configured)
    if config.file_path:
        try:
            # Ensure log directory exists
            log_path = Path(config.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                config.file_path,
                maxBytes=config.max_file_size_mb * 1024 * 1024,
                backupCount=config.backup_count
            )
            file_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # Fall back to console-only logging
            root_logger.warning(f"Failed to setup file logging: {e}")
    
    # Set specific logger levels
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    # Application loggers
    logging.getLogger("network_rag").setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    root_logger.info("Logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module"""
    return logging.getLogger(f"network_rag.{name}")


class StructuredLogger:
    """Structured logger with context support"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.context = {}
    
    def with_context(self, **kwargs) -> 'StructuredLogger':
        """Create logger with additional context"""
        new_logger = StructuredLogger(self.logger.name.replace("network_rag.", ""))
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def _format_message(self, message: str) -> str:
        """Format message with context"""
        if not self.context:
            return message
        
        context_str = " | ".join([f"{k}={v}" for k, v in self.context.items()])
        return f"{message} [{context_str}]"
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        ctx_logger = self.with_context(**kwargs) if kwargs else self
        ctx_logger.logger.debug(ctx_logger._format_message(message))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        ctx_logger = self.with_context(**kwargs) if kwargs else self
        ctx_logger.logger.info(ctx_logger._format_message(message))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        ctx_logger = self.with_context(**kwargs) if kwargs else self
        ctx_logger.logger.warning(ctx_logger._format_message(message))
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        ctx_logger = self.with_context(**kwargs) if kwargs else self
        ctx_logger.logger.error(ctx_logger._format_message(message))
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        ctx_logger = self.with_context(**kwargs) if kwargs else self
        ctx_logger.logger.critical(ctx_logger._format_message(message))