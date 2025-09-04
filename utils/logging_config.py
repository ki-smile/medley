"""
Logging configuration for MEDLEY Web Application
Provides structured logging with error tracking and monitoring
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
import json
import traceback

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'path': record.pathname,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add custom fields if present
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_obj['session_id'] = record.session_id
        if hasattr(record, 'case_id'):
            log_obj['case_id'] = record.case_id
        if hasattr(record, 'model_name'):
            log_obj['model_name'] = record.model_name
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_obj['ip_address'] = record.ip_address
        
        return json.dumps(log_obj)

class ErrorTracker:
    """Track and aggregate errors for monitoring"""
    
    def __init__(self, max_errors=1000):
        self.errors = []
        self.max_errors = max_errors
        self.error_counts = {}
        
    def track_error(self, error_type, error_message, context=None):
        """Track an error occurrence"""
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': error_type,
            'message': error_message,
            'context': context or {}
        }
        
        self.errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Update error counts
        error_key = f"{error_type}:{error_message[:50]}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
    def get_error_summary(self):
        """Get summary of recent errors"""
        return {
            'total_errors': len(self.errors),
            'unique_errors': len(self.error_counts),
            'top_errors': sorted(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            'recent_errors': self.errors[-10:]
        }
    
    def clear_old_errors(self, hours=24):
        """Clear errors older than specified hours"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        self.errors = [
            e for e in self.errors 
            if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff
        ]

# Global error tracker instance
error_tracker = ErrorTracker()

def setup_logging(app_name='medley', log_level='INFO'):
    """
    Setup comprehensive logging configuration
    
    Args:
        app_name: Name of the application
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    
    # Configure root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Console formatter
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_handler.setFormatter(logging.Formatter(console_format))
    
    # File handler for all logs (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / f'{app_name}.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    
    # Error file handler (rotating)
    error_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / f'{app_name}_errors.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    # Log uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Track in error tracker
        error_tracker.track_error(
            exc_type.__name__,
            str(exc_value),
            {'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback)}
        )
    
    sys.excepthook = handle_exception
    
    # Configure other loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logger

def log_request(logger, request, session_id=None):
    """Log incoming HTTP request"""
    logger.info(
        f"Request: {request.method} {request.path}",
        extra={
            'request_id': request.headers.get('X-Request-Id'),
            'session_id': session_id,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
    )

def log_response(logger, response, duration=None):
    """Log outgoing HTTP response"""
    logger.info(
        f"Response: {response.status_code}",
        extra={
            'status_code': response.status_code,
            'duration_ms': duration,
            'content_length': response.content_length
        }
    )

def log_error(logger, error, context=None):
    """Log and track an error"""
    logger.error(
        str(error),
        exc_info=True,
        extra=context or {}
    )
    
    # Track in error tracker
    error_tracker.track_error(
        type(error).__name__,
        str(error),
        context
    )

def log_model_call(logger, model_name, case_id, response_time=None, tokens=None, error=None):
    """Log model API call"""
    if error:
        logger.error(
            f"Model call failed: {model_name}",
            extra={
                'model_name': model_name,
                'case_id': case_id,
                'error': str(error)
            }
        )
    else:
        logger.info(
            f"Model call successful: {model_name}",
            extra={
                'model_name': model_name,
                'case_id': case_id,
                'response_time': response_time,
                'tokens': tokens
            }
        )

def get_error_report():
    """Get current error report for monitoring"""
    return error_tracker.get_error_summary()

# Performance monitoring
class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'request_times': [],
            'model_response_times': {},
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'error_count': 0
        }
    
    def record_request(self, duration_ms):
        """Record request duration"""
        self.metrics['request_times'].append(duration_ms)
        self.metrics['total_requests'] += 1
        
        # Keep only recent times (last 1000)
        if len(self.metrics['request_times']) > 1000:
            self.metrics['request_times'] = self.metrics['request_times'][-1000:]
    
    def record_model_time(self, model_name, duration_ms):
        """Record model response time"""
        if model_name not in self.metrics['model_response_times']:
            self.metrics['model_response_times'][model_name] = []
        
        self.metrics['model_response_times'][model_name].append(duration_ms)
        
        # Keep only recent times
        if len(self.metrics['model_response_times'][model_name]) > 100:
            self.metrics['model_response_times'][model_name] = \
                self.metrics['model_response_times'][model_name][-100:]
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics['cache_misses'] += 1
    
    def record_error(self):
        """Record error occurrence"""
        self.metrics['error_count'] += 1
    
    def get_metrics(self):
        """Get performance metrics summary"""
        avg_request_time = (
            sum(self.metrics['request_times']) / len(self.metrics['request_times'])
            if self.metrics['request_times'] else 0
        )
        
        cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (
            self.metrics['cache_hits'] / cache_total * 100
            if cache_total > 0 else 0
        )
        
        return {
            'avg_request_time_ms': avg_request_time,
            'total_requests': self.metrics['total_requests'],
            'error_rate': (
                self.metrics['error_count'] / self.metrics['total_requests'] * 100
                if self.metrics['total_requests'] > 0 else 0
            ),
            'cache_hit_rate': cache_hit_rate,
            'model_performance': {
                model: sum(times) / len(times) if times else 0
                for model, times in self.metrics['model_response_times'].items()
            }
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Export key components
__all__ = [
    'setup_logging',
    'log_request',
    'log_response',
    'log_error',
    'log_model_call',
    'get_error_report',
    'error_tracker',
    'performance_monitor',
    'JSONFormatter'
]