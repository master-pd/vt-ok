"""
Advanced Logging System for VT ULTRA PRO
"""
import logging
import logging.handlers
from logging import Logger
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import traceback
import inspect
import gzip
import threading
from pathlib import Path

class StructuredLogger:
    """Structured logging with multiple destinations"""
    
    def __init__(self, name: str = "VT_ULTRA_PRO", config: Dict = None):
        self.name = name
        self.config = config or self._default_config()
        self.logger = self._setup_logger()
        self._setup_handlers()
        self._performance_stats = {}
        
    def _default_config(self) -> Dict:
        """Default logging configuration"""
        return {
            'log_level': 'INFO',
            'log_file': 'logs/vt_ultra_pro.log',
            'error_file': 'logs/errors.log',
            'audit_file': 'logs/audit.log',
            'performance_file': 'logs/performance.log',
            'max_file_size_mb': 100,
            'backup_count': 5,
            'json_format': True,
            'console_output': True,
            'syslog_enabled': False,
            'syslog_host': 'localhost',
            'syslog_port': 514,
            'logstash_enabled': False,
            'logstash_host': 'localhost',
            'logstash_port': 5000,
            'sentry_enabled': False,
            'sentry_dsn': None,
            'metrics_enabled': True
        }
    
    def _setup_logger(self) -> Logger:
        """Setup logger instance"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.config['log_level']))
        logger.propagate = False
        
        # Remove existing handlers
        logger.handlers.clear()
        
        return logger
    
    def _setup_handlers(self):
        """Setup log handlers"""
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # File handler for general logs
        if self.config.get('log_file'):
            file_handler = logging.handlers.RotatingFileHandler(
                self.config['log_file'],
                maxBytes=self.config['max_file_size_mb'] * 1024 * 1024,
                backupCount=self.config['backup_count']
            )
            file_handler.setLevel(logging.INFO)
            
            if self.config['json_format']:
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(StructuredFormatter())
            
            self.logger.addHandler(file_handler)
        
        # Error file handler
        if self.config.get('error_file'):
            error_handler = logging.handlers.RotatingFileHandler(
                self.config['error_file'],
                maxBytes=self.config['max_file_size_mb'] * 1024 * 1024,
                backupCount=self.config['backup_count']
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(error_handler)
        
        # Audit log handler
        if self.config.get('audit_file'):
            audit_handler = AuditFileHandler(
                self.config['audit_file'],
                maxBytes=self.config['max_file_size_mb'] * 1024 * 1024,
                backupCount=self.config['backup_count']
            )
            audit_handler.setLevel(logging.INFO)
            audit_handler.setFormatter(AuditFormatter())
            self.logger.addHandler(audit_handler)
        
        # Performance log handler
        if self.config.get('performance_file'):
            perf_handler = PerformanceFileHandler(
                self.config['performance_file'],
                maxBytes=self.config['max_file_size_mb'] * 1024 * 1024,
                backupCount=self.config['backup_count']
            )
            perf_handler.setLevel(logging.INFO)
            perf_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(perf_handler)
        
        # Console handler
        if self.config.get('console_output', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(ColoredFormatter())
            self.logger.addHandler(console_handler)
        
        # Syslog handler
        if self.config.get('syslog_enabled'):
            try:
                syslog_handler = logging.handlers.SysLogHandler(
                    address=(self.config['syslog_host'], self.config['syslog_port'])
                )
                syslog_handler.setLevel(logging.WARNING)
                syslog_handler.setFormatter(SyslogFormatter())
                self.logger.addHandler(syslog_handler)
            except Exception as e:
                self.logger.error(f"Failed to setup syslog: {e}")
        
        # Logstash handler
        if self.config.get('logstash_enabled'):
            try:
                from logstash_async.handler import AsynchronousLogstashHandler
                
                logstash_handler = AsynchronousLogstashHandler(
                    self.config['logstash_host'],
                    self.config['logstash_port'],
                    database_path='logs/logstash.db'
                )
                logstash_handler.setLevel(logging.INFO)
                self.logger.addHandler(logstash_handler)
            except ImportError:
                self.logger.warning("Logstash handler not available")
            except Exception as e:
                self.logger.error(f"Failed to setup logstash: {e}")
        
        # Sentry handler (error tracking)
        if self.config.get('sentry_enabled') and self.config.get('sentry_dsn'):
            try:
                import sentry_sdk
                from sentry_sdk.integrations.logging import LoggingIntegration
                
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
                
                sentry_sdk.init(
                    dsn=self.config['sentry_dsn'],
                    integrations=[sentry_logging],
                    traces_sample_rate=1.0
                )
            except ImportError:
                self.logger.warning("Sentry SDK not available")
            except Exception as e:
                self.logger.error(f"Failed to setup Sentry: {e}")
    
    # Logging methods
    def info(self, message: str, extra: Dict = None, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, extra, **kwargs)
    
    def debug(self, message: str, extra: Dict = None, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, extra, **kwargs)
    
    def warning(self, message: str, extra: Dict = None, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, extra, **kwargs)
    
    def error(self, message: str, extra: Dict = None, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, extra, **kwargs)
    
    def critical(self, message: str, extra: Dict = None, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, extra, **kwargs)
    
    def exception(self, message: str, exc_info: bool = True, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, exc_info=exc_info, extra=self._build_extra(**kwargs))
    
    def audit(self, action: str, user: str, resource: str, 
              status: str = 'success', details: Dict = None):
        """Log audit trail"""
        audit_data = {
            'action': action,
            'user': user,
            'resource': resource,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        
        # Special audit logger
        audit_logger = logging.getLogger(f"{self.name}.audit")
        audit_logger.info(json.dumps(audit_data))
    
    def performance(self, operation: str, duration_ms: float, 
                   metrics: Dict = None, **kwargs):
        """Log performance metrics"""
        perf_data = {
            'operation': operation,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics or {},
            **kwargs
        }
        
        # Update performance statistics
        self._update_performance_stats(operation, duration_ms)
        
        # Special performance logger
        perf_logger = logging.getLogger(f"{self.name}.performance")
        perf_logger.info(json.dumps(perf_data))
    
    def _log(self, level: int, message: str, extra: Dict = None, **kwargs):
        """Internal log method"""
        if extra is None:
            extra = {}
        
        # Merge extra and kwargs
        log_extra = {**extra, **kwargs}
        
        # Add caller information
        if 'caller' not in log_extra:
            log_extra['caller'] = self._get_caller_info()
        
        # Add thread information
        log_extra['thread'] = threading.current_thread().name
        log_extra['thread_id'] = threading.get_ident()
        
        # Add process information
        log_extra['process_id'] = os.getpid()
        
        # Add timestamp
        log_extra['timestamp'] = datetime.utcnow().isoformat()
        
        # Log with extra context
        self.logger.log(level, message, extra=log_extra)
    
    def _build_extra(self, **kwargs) -> Dict:
        """Build extra logging context"""
        extra = kwargs.copy()
        
        # Add default fields
        extra.setdefault('timestamp', datetime.utcnow().isoformat())
        extra.setdefault('logger', self.name)
        extra.setdefault('caller', self._get_caller_info())
        
        return extra
    
    def _get_caller_info(self) -> str:
        """Get caller function information"""
        try:
            # Get the frame that called the log method
            frame = inspect.currentframe()
            # Go back through frames to find the actual caller
            for _ in range(5):  # Look back up to 5 frames
                frame = frame.f_back
                if frame is None:
                    break
                
                # Check if this frame is in our logger module
                module = inspect.getmodule(frame)
                if module and 'logger' not in module.__name__:
                    # Found the caller outside logger module
                    filename = Path(frame.f_code.co_filename).name
                    return f"{filename}:{frame.f_lineno}"
        except:
            pass
        
        return "unknown:0"
    
    def _update_performance_stats(self, operation: str, duration_ms: float):
        """Update performance statistics"""
        if operation not in self._performance_stats:
            self._performance_stats[operation] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'last_time': 0
            }
        
        stats = self._performance_stats[operation]
        stats['count'] += 1
        stats['total_time'] += duration_ms
        stats['min_time'] = min(stats['min_time'], duration_ms)
        stats['max_time'] = max(stats['max_time'], duration_ms)
        stats['last_time'] = duration_ms
        stats['avg_time'] = stats['total_time'] / stats['count']
    
    def get_performance_report(self) -> Dict:
        """Get performance statistics report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'operations': {},
            'summary': {
                'total_operations': sum(stats['count'] for stats in self._performance_stats.values()),
                'avg_response_time': 0
            }
        }
        
        total_time = 0
        total_count = 0
        
        for operation, stats in self._performance_stats.items():
            report['operations'][operation] = {
                'call_count': stats['count'],
                'avg_response_time_ms': stats.get('avg_time', 0),
                'min_response_time_ms': stats.get('min_time', 0),
                'max_response_time_ms': stats.get('max_time', 0),
                'last_response_time_ms': stats.get('last_time', 0),
                'total_time_ms': stats.get('total_time', 0)
            }
            
            total_time += stats.get('total_time', 0)
            total_count += stats.get('count', 0)
        
        if total_count > 0:
            report['summary']['avg_response_time'] = total_time / total_count
        
        return report
    
    def log_structured(self, data: Dict, level: int = logging.INFO):
        """Log structured data"""
        if not isinstance(data, dict):
            data = {'message': str(data)}
        
        message = data.pop('message', 'Structured log entry')
        self._log(level, message, extra=data)
    
    def start_timer(self, operation: str) -> 'TimerContext':
        """Start performance timer"""
        return TimerContext(self, operation)
    
    def export_logs(self, start_date: str, end_date: str, 
                   log_type: str = 'all', format: str = 'json') -> str:
        """Export logs for period"""
        log_file = self._get_log_file(log_type)
        if not log_file or not os.path.exists(log_file):
            return ""
        
        exported_logs = []
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    log_time = log_entry.get('timestamp', '')
                    
                    if start_date <= log_time <= end_date:
                        exported_logs.append(log_entry)
                except:
                    continue
        
        if format == 'json':
            return json.dumps(exported_logs, indent=2)
        elif format == 'csv':
            import pandas as pd
            df = pd.DataFrame(exported_logs)
            return df.to_csv(index=False)
        elif format == 'gzip':
            compressed = gzip.compress(json.dumps(exported_logs).encode())
            return base64.b64encode(compressed).decode()
        else:
            return str(exported_logs)
    
    def _get_log_file(self, log_type: str) -> Optional[str]:
        """Get log file path for type"""
        file_map = {
            'general': self.config.get('log_file'),
            'error': self.config.get('error_file'),
            'audit': self.config.get('audit_file'),
            'performance': self.config.get('performance_file')
        }
        
        if log_type == 'all':
            return self.config.get('log_file')
        
        return file_map.get(log_type)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Cleanup old log files"""
        log_dir = 'logs'
        
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            
            if os.path.isfile(filepath):
                # Check file age
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                file_age = (datetime.now() - file_time).days
                
                if file_age > days_to_keep and filename.endswith('.log'):
                    try:
                        os.remove(filepath)
                        self.info(f"Removed old log file: {filename}")
                    except Exception as e:
                        self.error(f"Failed to remove log file {filename}: {e}")
    
    def set_log_level(self, level: str):
        """Set log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if level.upper() in valid_levels:
            self.logger.setLevel(getattr(logging, level.upper()))
            for handler in self.logger.handlers:
                handler.setLevel(getattr(logging, level.upper()))
            self.config['log_level'] = level.upper()
        else:
            self.error(f"Invalid log level: {level}")
    
    def get_logger_stats(self) -> Dict:
        """Get logger statistics"""
        stats = {
            'name': self.name,
            'level': self.config['log_level'],
            'handlers': len(self.logger.handlers),
            'performance_stats': self.get_performance_report(),
            'log_files': []
        }
        
        # Check log files
        for handler in self.logger.handlers:
            if hasattr(handler, 'baseFilename'):
                filename = handler.baseFilename
                if os.path.exists(filename):
                    size_mb = os.path.getsize(filename) / (1024 * 1024)
                    stats['log_files'].append({
                        'filename': os.path.basename(filename),
                        'size_mb': round(size_mb, 2),
                        'path': filename
                    })
        
        return stats

# Custom Formatters
class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_data.update(record.extra)
        else:
            # Extract extra fields from record
            for key, value in record.__dict__.items():
                if key not in ['args', 'msg', 'levelno', 'levelname', 'name', 
                              'message', 'exc_info', 'exc_text', 'stack_info',
                              'thread', 'threadName', 'processName', 'process',
                              'module', 'funcName', 'lineno', 'created', 'msecs',
                              'relativeCreated', 'asctime']:
                    if not key.startswith('_'):
                        log_data[key] = value
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data)

class StructuredFormatter(logging.Formatter):
    """Structured text formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname.ljust(8)
        logger = record.name
        
        message = record.getMessage()
        
        # Add extra fields
        extra_parts = []
        for key, value in record.__dict__.items():
            if key not in ['args', 'msg', 'levelno', 'levelname', 'name', 
                          'message', 'exc_info', 'exc_text', 'stack_info',
                          'thread', 'threadName', 'processName', 'process',
                          'module', 'funcName', 'lineno', 'created', 'msecs',
                          'relativeCreated', 'asctime']:
                if not key.startswith('_'):
                    extra_parts.append(f"{key}={value}")
        
        if extra_parts:
            message = f"{message} | {' '.join(extra_parts)}"
        
        return f"{timestamp} | {level} | {logger} | {message}"

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[94m',      # Blue
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[95m'    # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level = record.levelname
        
        # Colorize level
        color = self.COLORS.get(level, '')
        colored_level = f"{color}{level:8}{self.RESET}"
        
        # Shorten logger name
        logger = record.name.split('.')[-1][:15]
        
        message = record.getMessage()
        
        return f"{timestamp} | {colored_level} | {logger:15} | {message}"

class AuditFormatter(logging.Formatter):
    """Audit log formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format audit log"""
        try:
            audit_data = json.loads(record.getMessage())
            
            timestamp = audit_data.get('timestamp', '')
            user = audit_data.get('user', 'unknown')
            action = audit_data.get('action', '')
            resource = audit_data.get('resource', '')
            status = audit_data.get('status', '')
            
            status_color = '\033[92m' if status == 'success' else '\033[91m'
            reset = '\033[0m'
            
            return f"{timestamp} | AUDIT | {user} | {action} | {resource} | {status_color}{status}{reset}"
        except:
            return record.getMessage()

class SyslogFormatter(logging.Formatter):
    """Syslog formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format for syslog"""
        return f"{record.name}[{record.process}]: {record.levelname}: {record.getMessage()}"

# Special Handlers
class AuditFileHandler(logging.handlers.RotatingFileHandler):
    """Audit log file handler"""
    
    def emit(self, record: logging.LogRecord):
        """Emit audit log record"""
        try:
            # Validate audit data
            audit_data = json.loads(record.getMessage())
            required_fields = ['action', 'user', 'resource', 'timestamp']
            
            if all(field in audit_data for field in required_fields):
                super().emit(record)
        except:
            pass

class PerformanceFileHandler(logging.handlers.RotatingFileHandler):
    """Performance log file handler"""
    
    def emit(self, record: logging.LogRecord):
        """Emit performance log record"""
        try:
            perf_data = json.loads(record.getMessage())
            
            # Validate required fields
            if 'operation' in perf_data and 'duration_ms' in perf_data:
                super().emit(record)
        except:
            pass

# Context Manager for Performance Timing
class TimerContext:
    """Context manager for performance timing"""
    
    def __init__(self, logger: StructuredLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration_ms = (end_time - self.start_time).total_seconds() * 1000
        
        # Log performance
        self.logger.performance(
            operation=self.operation,
            duration_ms=duration_ms,
            status='error' if exc_type else 'success'
        )
        
        # Also log as debug
        self.logger.debug(
            f"Operation '{self.operation}' completed in {duration_ms:.2f}ms",
            operation=self.operation,
            duration_ms=duration_ms
        )

# Global logger instance
_logger_instance = None

def get_logger(name: str = "VT_ULTRA_PRO", config: Dict = None) -> StructuredLogger:
    """Get or create logger instance"""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = StructuredLogger(name, config)
    
    return _logger_instance

def setup_logging(config: Dict = None):
    """Setup global logging configuration"""
    global _logger_instance
    _logger_instance = StructuredLogger(config=config)
    
    # Also configure root logger
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return _logger_instance

# Utility functions
def log_exception(logger: StructuredLogger, message: str = "Exception occurred"):
    """Decorator to log exceptions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"{message}: {str(e)}")
                raise
        return wrapper
    return decorator

def log_performance(logger: StructuredLogger, operation: str = None):
    """Decorator to log performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            
            with logger.start_timer(op_name):
                result = func(*args, **kwargs)
            
            return result
        return wrapper
    return decorator