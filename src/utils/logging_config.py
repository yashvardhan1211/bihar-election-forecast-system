import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from src.config.settings import Config


class ProductionLogger:
    """Production-ready logging configuration with rotation and monitoring"""
    
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configure logging levels
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Setup loggers
        self._setup_main_logger()
        self._setup_error_logger()
        self._setup_performance_logger()
        
        print(f"✅ Production logging configured (Level: {self.log_level})")
    
    def _setup_main_logger(self):
        """Setup main application logger with rotation"""
        main_logger = logging.getLogger('bihar_forecast')
        main_logger.setLevel(getattr(logging, self.log_level))
        
        # Remove existing handlers
        main_logger.handlers.clear()
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / 'bihar_forecast.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        main_logger.addHandler(file_handler)
        main_logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        main_logger.propagate = False
    
    def _setup_error_logger(self):
        """Setup dedicated error logger"""
        error_logger = logging.getLogger('bihar_forecast.errors')
        error_logger.setLevel(logging.ERROR)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / 'errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10
        )
        
        # Error formatter with more details
        error_formatter = logging.Formatter(
            '%(asctime)s - ERROR - %(name)s - %(funcName)s:%(lineno)d\n'
            'Message: %(message)s\n'
            'Exception: %(exc_info)s\n'
            '---'
        )
        
        error_handler.setFormatter(error_formatter)
        error_logger.addHandler(error_handler)
        error_logger.propagate = False
    
    def _setup_performance_logger(self):
        """Setup performance monitoring logger"""
        perf_logger = logging.getLogger('bihar_forecast.performance')
        perf_logger.setLevel(logging.INFO)
        
        # Performance file handler
        perf_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / 'performance.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        
        # Performance formatter
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s'
        )
        
        perf_handler.setFormatter(perf_formatter)
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False
    
    @staticmethod
    def get_logger(name: str = 'bihar_forecast'):
        """Get configured logger instance"""
        return logging.getLogger(name)
    
    @staticmethod
    def log_performance(operation: str, duration: float, details: dict = None):
        """Log performance metrics"""
        perf_logger = logging.getLogger('bihar_forecast.performance')
        
        message = f"Operation: {operation} | Duration: {duration:.3f}s"
        if details:
            message += f" | Details: {details}"
        
        perf_logger.info(message)
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """Log error with context"""
        error_logger = logging.getLogger('bihar_forecast.errors')
        
        message = f"Context: {context}" if context else "Unhandled error"
        error_logger.error(message, exc_info=error)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days"""
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        
        cleaned_count = 0
        for log_file in self.logs_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned_count += 1
        
        if cleaned_count > 0:
            main_logger = self.get_logger()
            main_logger.info(f"Cleaned up {cleaned_count} old log files")


# Initialize production logging
def setup_production_logging():
    """Initialize production logging configuration"""
    return ProductionLogger()


# Context manager for performance logging
class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, details: dict = None):
        self.operation_name = operation_name
        self.details = details or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is not None:
            self.details['error'] = str(exc_val)
            self.details['success'] = False
        else:
            self.details['success'] = True
        
        ProductionLogger.log_performance(
            self.operation_name, 
            duration, 
            self.details
        )


# Decorator for automatic performance logging
def log_performance(operation_name: str = None):
    """Decorator to automatically log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with PerformanceTimer(op_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator