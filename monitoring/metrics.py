"""
Monitoring and Metrics Module for Naebak Gateway

This module provides comprehensive monitoring capabilities including:
- Prometheus metrics collection
- Custom business metrics
- Performance monitoring
- Error tracking
"""

from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, Gauge, Info
import time
import functools
from flask import request, g
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class GatewayMetrics:
    """
    Centralized metrics collection for the Naebak Gateway
    """
    
    def __init__(self, app=None):
        self.app = app
        self.metrics = None
        
        # Custom metrics
        self.request_count = Counter(
            'gateway_requests_total',
            'Total number of requests processed by gateway',
            ['method', 'endpoint', 'service', 'status_code']
        )
        
        self.request_duration = Histogram(
            'gateway_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint', 'service'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.active_connections = Gauge(
            'gateway_active_connections',
            'Number of active connections'
        )
        
        self.service_health = Gauge(
            'gateway_service_health',
            'Health status of backend services (1=healthy, 0=unhealthy)',
            ['service_name']
        )
        
        self.rate_limit_hits = Counter(
            'gateway_rate_limit_hits_total',
            'Number of rate limit hits',
            ['endpoint', 'limit_type']
        )
        
        self.authentication_attempts = Counter(
            'gateway_auth_attempts_total',
            'Authentication attempts',
            ['status', 'endpoint']
        )
        
        self.proxy_errors = Counter(
            'gateway_proxy_errors_total',
            'Proxy errors by service',
            ['service', 'error_type']
        )
        
        self.gateway_info = Info(
            'gateway_info',
            'Gateway information'
        )
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize metrics with Flask app"""
        self.app = app
        
        # Initialize Prometheus Flask Exporter
        self.metrics = PrometheusMetrics(app)
        
        # Set gateway info
        self.gateway_info.info({
            'version': app.config.get('APP_VERSION', '1.0.0'),
            'name': 'naebak-gateway'
        })
        
        # Register request hooks
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        logger.info("Gateway metrics initialized successfully")
    
    def _before_request(self):
        """Hook executed before each request"""
        g.start_time = time.time()
        self.active_connections.inc()
    
    def _after_request(self, response):
        """Hook executed after each request"""
        try:
            # Calculate request duration
            duration = time.time() - g.get('start_time', time.time())
            
            # Extract request information
            method = request.method
            endpoint = request.endpoint or 'unknown'
            service = self._extract_service_name(request.path)
            status_code = str(response.status_code)
            
            # Record metrics
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                service=service,
                status_code=status_code
            ).inc()
            
            self.request_duration.labels(
                method=method,
                endpoint=endpoint,
                service=service
            ).observe(duration)
            
            self.active_connections.dec()
            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
        
        return response
    
    def _extract_service_name(self, path):
        """Extract service name from request path"""
        if path.startswith('/api/'):
            parts = path.split('/')
            if len(parts) >= 3:
                return f"naebak-{parts[2]}-service"
        return "unknown"
    
    def record_rate_limit_hit(self, endpoint, limit_type):
        """Record rate limit hit"""
        self.rate_limit_hits.labels(
            endpoint=endpoint,
            limit_type=limit_type
        ).inc()
    
    def record_auth_attempt(self, status, endpoint):
        """Record authentication attempt"""
        self.authentication_attempts.labels(
            status=status,
            endpoint=endpoint
        ).inc()
    
    def record_proxy_error(self, service, error_type):
        """Record proxy error"""
        self.proxy_errors.labels(
            service=service,
            error_type=error_type
        ).inc()
    
    def update_service_health(self, service_name, is_healthy):
        """Update service health status"""
        self.service_health.labels(service_name=service_name).set(1 if is_healthy else 0)
    
    def get_metrics_summary(self):
        """Get a summary of current metrics"""
        return {
            'active_connections': self.active_connections._value._value,
            'total_requests': sum([
                sample.value for sample in self.request_count.collect()[0].samples
            ]),
            'services_monitored': len(self.service_health._metrics)
        }


def monitor_performance(func):
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Performance monitoring error in {func.__name__}: {e}")
            raise
        finally:
            duration = time.time() - start_time
            logger.debug(f"Function {func.__name__} took {duration:.4f} seconds")
    return wrapper


def track_service_call(service_name):
    """Decorator to track service calls"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # Record successful call
                return result
            except Exception as e:
                # Record failed call
                logger.error(f"Service call to {service_name} failed: {e}")
                raise
            finally:
                duration = time.time() - start_time
                logger.info(f"Service call to {service_name} completed in {duration:.4f}s")
        return wrapper
    return decorator
