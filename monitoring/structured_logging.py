import time
"""
Structured Logging System for Naebak Gateway

This module provides structured logging capabilities including:
- JSON formatted logs
- Correlation IDs for request tracing
- Performance logging
- Error tracking and alerting
"""

import structlog
import logging
import json
import uuid
from datetime import datetime
from flask import request, g, has_request_context
from typing import Dict, Any, Optional
import sys
import os

class CorrelationIDProcessor:
    """Add correlation ID to log entries"""
    
    def __call__(self, logger, method_name, event_dict):
        if has_request_context():
            # Get or create correlation ID for this request
            correlation_id = getattr(g, 'correlation_id', None)
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
                g.correlation_id = correlation_id
            
            event_dict['correlation_id'] = correlation_id
            event_dict['request_id'] = correlation_id
        
        return event_dict

class RequestContextProcessor:
    """Add request context information to log entries"""
    
    def __call__(self, logger, method_name, event_dict):
        if has_request_context():
            event_dict.update({
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'content_type': request.content_type,
            })
            
            # Add user info if available
            if hasattr(g, 'current_user') and g.current_user:
                event_dict['user_id'] = getattr(g.current_user, 'id', None)
                event_dict['user_type'] = getattr(g.current_user, 'user_type', None)
        
        return event_dict

class TimestampProcessor:
    """Add ISO timestamp to log entries"""
    
    def __call__(self, logger, method_name, event_dict):
        event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        return event_dict

class ServiceContextProcessor:
    """Add service context information"""
    
    def __init__(self, service_name: str, version: str):
        self.service_name = service_name
        self.version = version
    
    def __call__(self, logger, method_name, event_dict):
        event_dict.update({
            'service': self.service_name,
            'version': self.version,
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'hostname': os.getenv('HOSTNAME', 'unknown')
        })
        return event_dict

class PerformanceLogger:
    """Logger for performance metrics and timing"""
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    def log_request_performance(self, duration: float, service: str, endpoint: str, status_code: int):
        """Log request performance metrics"""
        self.logger.info(
            "request_performance",
            duration=duration,
            service=service,
            endpoint=endpoint,
            status_code=status_code,
            performance_category=self._categorize_performance(duration)
        )
    
    def log_service_call_performance(self, service: str, operation: str, duration: float, success: bool):
        """Log service call performance"""
        self.logger.info(
            "service_call_performance",
            service=service,
            operation=operation,
            duration=duration,
            success=success,
            performance_category=self._categorize_performance(duration)
        )
    
    def _categorize_performance(self, duration: float) -> str:
        """Categorize performance based on duration"""
        if duration < 0.1:
            return "excellent"
        elif duration < 0.5:
            return "good"
        elif duration < 1.0:
            return "acceptable"
        elif duration < 2.0:
            return "slow"
        else:
            return "very_slow"

class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self):
        self.logger = structlog.get_logger("security")
    
    def log_authentication_attempt(self, success: bool, user_id: Optional[str] = None, reason: Optional[str] = None):
        """Log authentication attempts"""
        self.logger.info(
            "authentication_attempt",
            success=success,
            user_id=user_id,
            reason=reason,
            security_event=True
        )
    
    def log_authorization_failure(self, user_id: Optional[str], resource: str, action: str):
        """Log authorization failures"""
        self.logger.warning(
            "authorization_failure",
            user_id=user_id,
            resource=resource,
            action=action,
            security_event=True
        )
    
    def log_rate_limit_exceeded(self, identifier: str, limit_type: str, endpoint: str):
        """Log rate limit violations"""
        self.logger.warning(
            "rate_limit_exceeded",
            identifier=identifier,
            limit_type=limit_type,
            endpoint=endpoint,
            security_event=True
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log suspicious activities"""
        self.logger.error(
            "suspicious_activity",
            activity_type=activity_type,
            details=details,
            security_event=True,
            alert_required=True
        )

class ErrorLogger:
    """Logger for errors and exceptions"""
    
    def __init__(self):
        self.logger = structlog.get_logger("error")
    
    def log_application_error(self, error: Exception, context: Optional[Dict] = None):
        """Log application errors"""
        self.logger.error(
            "application_error",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {},
            stack_trace=self._get_stack_trace(error)
        )
    
    def log_service_error(self, service: str, operation: str, error: Exception):
        """Log service-related errors"""
        self.logger.error(
            "service_error",
            service=service,
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=self._get_stack_trace(error)
        )
    
    def log_validation_error(self, field: str, value: Any, reason: str):
        """Log validation errors"""
        self.logger.warning(
            "validation_error",
            field=field,
            value=str(value)[:100],  # Limit value length
            reason=reason
        )
    
    def _get_stack_trace(self, error: Exception) -> Optional[str]:
        """Get stack trace from exception"""
        import traceback
        try:
            return traceback.format_exc()
        except:
            return None

class BusinessLogger:
    """Logger for business events and metrics"""
    
    def __init__(self):
        self.logger = structlog.get_logger("business")
    
    def log_user_action(self, user_id: str, action: str, resource: str, details: Optional[Dict] = None):
        """Log user actions"""
        self.logger.info(
            "user_action",
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {},
            business_event=True
        )
    
    def log_service_usage(self, service: str, operation: str, user_id: Optional[str] = None):
        """Log service usage"""
        self.logger.info(
            "service_usage",
            service=service,
            operation=operation,
            user_id=user_id,
            business_event=True
        )
    
    def log_gateway_routing(self, source_path: str, target_service: str, target_path: str):
        """Log gateway routing decisions"""
        self.logger.debug(
            "gateway_routing",
            source_path=source_path,
            target_service=target_service,
            target_path=target_path,
            business_event=True
        )

def setup_structured_logging(app, service_name: str = "naebak-gateway", version: str = "1.0.0"):
    """Setup structured logging for the Flask application"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            TimestampProcessor(),
            ServiceContextProcessor(service_name, version),
            CorrelationIDProcessor(),
            RequestContextProcessor(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Set up Flask request logging
    @app.before_request
    def before_request_logging():
        g.start_time = time.time()
        
        # Generate correlation ID if not present
        if not hasattr(g, 'correlation_id'):
            g.correlation_id = str(uuid.uuid4())
        
        # Log request start
        logger = structlog.get_logger("request")
        logger.info(
            "request_started",
            method=request.method,
            path=request.path,
            query_string=request.query_string.decode('utf-8') if request.query_string else None
        )
    
    @app.after_request
    def after_request_logging(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log request completion
            logger = structlog.get_logger("request")
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration=duration,
                content_length=response.content_length
            )
            
            # Log performance metrics
            perf_logger = PerformanceLogger()
            service = extract_service_from_path(request.path)
            perf_logger.log_request_performance(
                duration=duration,
                service=service,
                endpoint=request.endpoint or "unknown",
                status_code=response.status_code
            )
        
        return response
    
    # Create logger instances
    app.logger = structlog.get_logger("app")
    app.performance_logger = PerformanceLogger()
    app.security_logger = SecurityLogger()
    app.error_logger = ErrorLogger()
    app.business_logger = BusinessLogger()
    
    app.logger.info("Structured logging initialized successfully")

def extract_service_from_path(path: str) -> str:
    """Extract service name from request path"""
    if path.startswith('/api/'):
        parts = path.split('/')
        if len(parts) >= 3:
            return f"naebak-{parts[2]}-service"
    return "gateway"

def get_correlation_id() -> Optional[str]:
    """Get current request correlation ID"""
    if has_request_context():
        return getattr(g, 'correlation_id', None)
    return None

# Convenience functions for common logging patterns
def log_info(message: str, **kwargs):
    """Log info message with context"""
    logger = structlog.get_logger()
    logger.info(message, **kwargs)

def log_warning(message: str, **kwargs):
    """Log warning message with context"""
    logger = structlog.get_logger()
    logger.warning(message, **kwargs)

def log_error(message: str, **kwargs):
    """Log error message with context"""
    logger = structlog.get_logger()
    logger.error(message, **kwargs)

def log_debug(message: str, **kwargs):
    """Log debug message with context"""
    logger = structlog.get_logger()
    logger.debug(message, **kwargs)
