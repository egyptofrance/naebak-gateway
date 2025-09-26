"""
Advanced Health Checking System for Naebak Gateway

This module provides comprehensive health checking capabilities including:
- Service health monitoring
- Circuit breaker pattern
- Health check aggregation
- Dependency mapping
"""

import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker activated
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class HealthCheckResult:
    service_name: str
    status: ServiceStatus
    response_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    details: Dict = field(default_factory=dict)

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    timeout: int = 10  # seconds
    success_threshold: int = 3  # for half-open state

class CircuitBreaker:
    """Circuit breaker implementation for service calls"""
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig):
        self.service_name = service_name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
            return False
    
    def record_success(self):
        """Record successful request"""
        with self.lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    logger.info(f"Circuit breaker for {self.service_name} reset to CLOSED")
    
    def record_failure(self):
        """Record failed request"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker for {self.service_name} opened due to failures")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker for {self.service_name} reopened")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.config.recovery_timeout
    
    def get_state(self) -> Dict:
        """Get current circuit breaker state"""
        return {
            'service_name': self.service_name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }

class HealthChecker:
    """Advanced health checking system with circuit breaker support"""
    
    def __init__(self, services_config: Dict):
        self.services_config = services_config
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_history: Dict[str, List[HealthCheckResult]] = {}
        self.running = False
        self.check_thread = None
        self.lock = threading.Lock()
        
        # Initialize circuit breakers
        for service_name in services_config.keys():
            self.circuit_breakers[service_name] = CircuitBreaker(
                service_name, CircuitBreakerConfig()
            )
            self.health_history[service_name] = []
    
    def start_monitoring(self, check_interval: int = 30):
        """Start continuous health monitoring"""
        if self.running:
            return
        
        self.running = True
        self.check_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.check_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.running = False
        if self.check_thread:
            self.check_thread.join()
        logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self, check_interval: int):
        """Main monitoring loop"""
        while self.running:
            try:
                self.check_all_services()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short sleep on error
    
    def check_service_health(self, service_name: str) -> HealthCheckResult:
        """Check health of a specific service"""
        if service_name not in self.services_config:
            return HealthCheckResult(
                service_name=service_name,
                status=ServiceStatus.UNKNOWN,
                response_time=0,
                timestamp=datetime.now(),
                error_message="Service not configured"
            )
        
        service_config = self.services_config[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            return HealthCheckResult(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                response_time=0,
                timestamp=datetime.now(),
                error_message="Circuit breaker open",
                details={'circuit_state': circuit_breaker.state.value}
            )
        
        # Perform health check
        start_time = time.time()
        try:
            health_url = f"{service_config['base_url']}/health"
            response = requests.get(
                health_url,
                timeout=circuit_breaker.config.timeout,
                headers={'User-Agent': 'Naebak-Gateway-HealthChecker/1.0'}
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                circuit_breaker.record_success()
                
                # Parse response for additional details
                try:
                    details = response.json()
                except:
                    details = {}
                
                return HealthCheckResult(
                    service_name=service_name,
                    status=ServiceStatus.HEALTHY,
                    response_time=response_time,
                    timestamp=datetime.now(),
                    details=details
                )
            else:
                circuit_breaker.record_failure()
                return HealthCheckResult(
                    service_name=service_name,
                    status=ServiceStatus.UNHEALTHY,
                    response_time=response_time,
                    timestamp=datetime.now(),
                    error_message=f"HTTP {response.status_code}"
                )
        
        except requests.exceptions.Timeout:
            circuit_breaker.record_failure()
            return HealthCheckResult(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message="Request timeout"
            )
        
        except requests.exceptions.ConnectionError:
            circuit_breaker.record_failure()
            return HealthCheckResult(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message="Connection error"
            )
        
        except Exception as e:
            circuit_breaker.record_failure()
            return HealthCheckResult(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def check_all_services(self) -> Dict[str, HealthCheckResult]:
        """Check health of all configured services"""
        results = {}
        
        for service_name in self.services_config.keys():
            result = self.check_service_health(service_name)
            results[service_name] = result
            
            # Store in history
            with self.lock:
                self.health_history[service_name].append(result)
                # Keep only last 100 results
                if len(self.health_history[service_name]) > 100:
                    self.health_history[service_name] = self.health_history[service_name][-100:]
        
        return results
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get current status of a service"""
        with self.lock:
            history = self.health_history.get(service_name, [])
            if not history:
                return ServiceStatus.UNKNOWN
            return history[-1].status
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if service is currently healthy"""
        status = self.get_service_status(service_name)
        return status == ServiceStatus.HEALTHY
    
    def get_healthy_services(self) -> List[str]:
        """Get list of currently healthy services"""
        healthy_services = []
        for service_name in self.services_config.keys():
            if self.is_service_healthy(service_name):
                healthy_services.append(service_name)
        return healthy_services
    
    def get_circuit_breaker_states(self) -> Dict[str, Dict]:
        """Get current state of all circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self.circuit_breakers.items()
        }
    
    def get_health_summary(self) -> Dict:
        """Get overall health summary"""
        total_services = len(self.services_config)
        healthy_services = len(self.get_healthy_services())
        
        # Calculate average response time
        avg_response_times = {}
        with self.lock:
            for service_name, history in self.health_history.items():
                if history:
                    recent_results = [r for r in history[-10:] if r.status == ServiceStatus.HEALTHY]
                    if recent_results:
                        avg_response_times[service_name] = sum(r.response_time for r in recent_results) / len(recent_results)
        
        return {
            'total_services': total_services,
            'healthy_services': healthy_services,
            'unhealthy_services': total_services - healthy_services,
            'health_percentage': (healthy_services / total_services * 100) if total_services > 0 else 0,
            'average_response_times': avg_response_times,
            'circuit_breakers': self.get_circuit_breaker_states(),
            'last_check': datetime.now().isoformat()
        }
    
    def get_service_history(self, service_name: str, limit: int = 50) -> List[Dict]:
        """Get health check history for a service"""
        with self.lock:
            history = self.health_history.get(service_name, [])
            recent_history = history[-limit:] if history else []
            
            return [
                {
                    'timestamp': result.timestamp.isoformat(),
                    'status': result.status.value,
                    'response_time': result.response_time,
                    'error_message': result.error_message,
                    'details': result.details
                }
                for result in recent_history
            ]
