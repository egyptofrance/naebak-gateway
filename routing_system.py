"""
Advanced Routing System for Naebak Gateway

This module implements a sophisticated routing system that provides dynamic service discovery,
intelligent load balancing, and flexible routing rules for the Naebak platform. The system
supports multiple routing strategies and can adapt to service health and performance metrics.

Key Features:
- Dynamic service discovery and registration
- Multiple load balancing algorithms (round-robin, least connections, weighted)
- Health-based routing with automatic failover
- Route versioning and canary deployments
- Circuit breaker pattern for resilience
- Request/response transformation capabilities

Architecture:
The routing system uses a registry-based approach where services register themselves
with health information, and the gateway dynamically routes requests based on
availability, performance, and configured policies.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import requests
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    """
    Enumeration of available load balancing strategies.
    
    Each strategy implements a different algorithm for distributing requests
    across multiple service instances to optimize performance and reliability.
    """
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    IP_HASH = "ip_hash"

class ServiceStatus(Enum):
    """
    Enumeration of possible service health states.
    
    These states are used by the health monitoring system to determine
    whether a service instance should receive traffic.
    """
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

@dataclass
class ServiceInstance:
    """
    Represents a single instance of a microservice.
    
    This class contains all information needed to route requests to a service
    instance, including health status, performance metrics, and configuration.
    
    Attributes:
        id (str): Unique identifier for the service instance
        url (str): Base URL for the service instance
        weight (int): Weight for load balancing (higher = more traffic)
        status (ServiceStatus): Current health status
        last_health_check (datetime): Timestamp of last health check
        response_time (float): Average response time in milliseconds
        active_connections (int): Number of active connections
        error_rate (float): Error rate percentage (0-100)
        version (str): Service version for canary deployments
        metadata (Dict): Additional service metadata
    """
    id: str
    url: str
    weight: int = 1
    status: ServiceStatus = ServiceStatus.HEALTHY
    last_health_check: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    active_connections: int = 0
    error_rate: float = 0.0
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RouteRule:
    """
    Defines routing rules for a specific service or endpoint.
    
    Route rules determine how requests are matched and routed to service instances,
    including authentication requirements, rate limiting, and transformation rules.
    
    Attributes:
        pattern (str): URL pattern to match (supports wildcards)
        service_name (str): Target service name
        load_balancing (LoadBalancingStrategy): Load balancing strategy
        auth_required (bool): Whether authentication is required
        admin_only (bool): Whether admin privileges are required
        rate_limit (str): Rate limiting configuration
        timeout (int): Request timeout in seconds
        retry_count (int): Number of retry attempts
        circuit_breaker (bool): Whether to use circuit breaker
        canary_percentage (float): Percentage of traffic for canary deployment
        request_transform (Dict): Request transformation rules
        response_transform (Dict): Response transformation rules
    """
    pattern: str
    service_name: str
    load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    auth_required: bool = False
    admin_only: bool = False
    rate_limit: str = "100/minute"
    timeout: int = 30
    retry_count: int = 3
    circuit_breaker: bool = True
    canary_percentage: float = 0.0
    request_transform: Dict[str, Any] = field(default_factory=dict)
    response_transform: Dict[str, Any] = field(default_factory=dict)

class CircuitBreaker:
    """
    Implements the circuit breaker pattern for service resilience.
    
    The circuit breaker monitors service failures and automatically stops
    sending requests to failing services, allowing them time to recover.
    
    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Service is failing, requests are rejected
        - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize circuit breaker with configuration parameters.
        
        Args:
            failure_threshold (int): Number of failures before opening circuit
            recovery_timeout (int): Seconds to wait before testing recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self._lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """
        Execute a function call through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result if circuit is closed, raises exception if open
            
        Raises:
            Exception: If circuit is open or function fails
        """
        with self._lock:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful request - reset failure count and close circuit."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed request - increment failure count and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ServiceRegistry:
    """
    Manages service registration and discovery for the gateway.
    
    The service registry maintains a real-time view of all available service
    instances, their health status, and performance metrics. It provides
    the foundation for intelligent routing decisions.
    """
    
    def __init__(self):
        """Initialize the service registry with empty collections."""
        self.services: Dict[str, List[ServiceInstance]] = defaultdict(list)
        self.route_rules: Dict[str, RouteRule] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.load_balancer_state: Dict[str, Dict] = defaultdict(dict)
        self._lock = threading.RLock()
        
        # Performance tracking
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        logger.info("Service registry initialized")
    
    def register_service(self, service_name: str, instance: ServiceInstance):
        """
        Register a new service instance with the registry.
        
        Args:
            service_name (str): Name of the service
            instance (ServiceInstance): Service instance details
        """
        with self._lock:
            # Remove existing instance with same ID
            self.services[service_name] = [
                inst for inst in self.services[service_name] 
                if inst.id != instance.id
            ]
            
            # Add new instance
            self.services[service_name].append(instance)
            
            # Initialize circuit breaker if needed
            if service_name not in self.circuit_breakers:
                self.circuit_breakers[service_name] = CircuitBreaker()
            
            logger.info(f"Registered service instance: {service_name}/{instance.id}")
    
    def deregister_service(self, service_name: str, instance_id: str):
        """
        Remove a service instance from the registry.
        
        Args:
            service_name (str): Name of the service
            instance_id (str): ID of the instance to remove
        """
        with self._lock:
            original_count = len(self.services[service_name])
            self.services[service_name] = [
                inst for inst in self.services[service_name] 
                if inst.id != instance_id
            ]
            
            removed_count = original_count - len(self.services[service_name])
            if removed_count > 0:
                logger.info(f"Deregistered service instance: {service_name}/{instance_id}")
    
    def add_route_rule(self, pattern: str, rule: RouteRule):
        """
        Add a routing rule for URL pattern matching.
        
        Args:
            pattern (str): URL pattern to match
            rule (RouteRule): Routing rule configuration
        """
        with self._lock:
            self.route_rules[pattern] = rule
            logger.info(f"Added route rule: {pattern} -> {rule.service_name}")
    
    def find_route_rule(self, path: str) -> Optional[RouteRule]:
        """
        Find the matching route rule for a given path.
        
        Args:
            path (str): Request path to match
            
        Returns:
            Optional[RouteRule]: Matching route rule or None
        """
        with self._lock:
            # Exact match first
            if path in self.route_rules:
                return self.route_rules[path]
            
            # Pattern matching
            for pattern, rule in self.route_rules.items():
                if self._pattern_matches(pattern, path):
                    return rule
            
            return None
    
    def _pattern_matches(self, pattern: str, path: str) -> bool:
        """
        Check if a URL pattern matches a given path.
        
        Supports simple wildcard matching with * and prefix matching.
        
        Args:
            pattern (str): URL pattern (may contain wildcards)
            path (str): Request path to test
            
        Returns:
            bool: True if pattern matches path
        """
        if '*' in pattern:
            # Simple wildcard matching
            parts = pattern.split('*')
            if len(parts) == 2:
                prefix, suffix = parts
                return path.startswith(prefix) and path.endswith(suffix)
        
        # Prefix matching for API routes
        if pattern.endswith('/'):
            return path.startswith(pattern.rstrip('/'))
        
        return pattern == path
    
    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """
        Get all healthy instances for a service.
        
        Args:
            service_name (str): Name of the service
            
        Returns:
            List[ServiceInstance]: List of healthy service instances
        """
        with self._lock:
            instances = self.services.get(service_name, [])
            return [
                inst for inst in instances 
                if inst.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
            ]
    
    def select_instance(self, service_name: str, strategy: LoadBalancingStrategy, 
                       client_ip: str = None) -> Optional[ServiceInstance]:
        """
        Select a service instance using the specified load balancing strategy.
        
        Args:
            service_name (str): Name of the service
            strategy (LoadBalancingStrategy): Load balancing algorithm
            client_ip (str): Client IP for IP hash strategy
            
        Returns:
            Optional[ServiceInstance]: Selected instance or None if none available
        """
        healthy_instances = self.get_healthy_instances(service_name)
        
        if not healthy_instances:
            logger.warning(f"No healthy instances available for service: {service_name}")
            return None
        
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(service_name, healthy_instances)
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_instances)
        elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(service_name, healthy_instances)
        elif strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(healthy_instances)
        elif strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash_select(healthy_instances, client_ip)
        else:
            return healthy_instances[0]
    
    def _round_robin_select(self, service_name: str, 
                           instances: List[ServiceInstance]) -> ServiceInstance:
        """Round-robin load balancing implementation."""
        if 'round_robin_index' not in self.load_balancer_state[service_name]:
            self.load_balancer_state[service_name]['round_robin_index'] = 0
        
        index = self.load_balancer_state[service_name]['round_robin_index']
        selected = instances[index % len(instances)]
        self.load_balancer_state[service_name]['round_robin_index'] = (index + 1) % len(instances)
        
        return selected
    
    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections load balancing implementation."""
        return min(instances, key=lambda inst: inst.active_connections)
    
    def _weighted_round_robin_select(self, service_name: str, 
                                   instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round-robin load balancing implementation."""
        if 'weighted_counters' not in self.load_balancer_state[service_name]:
            self.load_balancer_state[service_name]['weighted_counters'] = {
                inst.id: 0 for inst in instances
            }
        
        counters = self.load_balancer_state[service_name]['weighted_counters']
        
        # Find instance with lowest counter relative to weight
        selected = min(instances, key=lambda inst: counters.get(inst.id, 0) / inst.weight)
        counters[selected.id] = counters.get(selected.id, 0) + 1
        
        return selected
    
    def _ip_hash_select(self, instances: List[ServiceInstance], 
                       client_ip: str) -> ServiceInstance:
        """IP hash load balancing implementation."""
        if not client_ip:
            return random.choice(instances)
        
        hash_value = hash(client_ip)
        index = hash_value % len(instances)
        return instances[index]
    
    def update_instance_metrics(self, service_name: str, instance_id: str, 
                              response_time: float, success: bool):
        """
        Update performance metrics for a service instance.
        
        Args:
            service_name (str): Name of the service
            instance_id (str): ID of the instance
            response_time (float): Response time in milliseconds
            success (bool): Whether the request was successful
        """
        with self._lock:
            instances = self.services.get(service_name, [])
            for instance in instances:
                if instance.id == instance_id:
                    # Update response time (moving average)
                    if instance.response_time == 0:
                        instance.response_time = response_time
                    else:
                        instance.response_time = (instance.response_time * 0.9) + (response_time * 0.1)
                    
                    # Track request history for error rate calculation
                    history = self.request_history[f"{service_name}/{instance_id}"]
                    history.append({
                        'timestamp': datetime.now(),
                        'success': success,
                        'response_time': response_time
                    })
                    
                    # Calculate error rate from recent history
                    recent_requests = [
                        req for req in history 
                        if (datetime.now() - req['timestamp']).seconds < 300  # Last 5 minutes
                    ]
                    
                    if recent_requests:
                        error_count = sum(1 for req in recent_requests if not req['success'])
                        instance.error_rate = (error_count / len(recent_requests)) * 100
                    
                    break
    
    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a service.
        
        Args:
            service_name (str): Name of the service
            
        Returns:
            Dict[str, Any]: Service statistics including instance count,
                          health status, and performance metrics
        """
        with self._lock:
            instances = self.services.get(service_name, [])
            
            if not instances:
                return {
                    'service_name': service_name,
                    'instance_count': 0,
                    'healthy_instances': 0,
                    'status': 'unavailable'
                }
            
            healthy_count = len([inst for inst in instances if inst.status == ServiceStatus.HEALTHY])
            avg_response_time = sum(inst.response_time for inst in instances) / len(instances)
            avg_error_rate = sum(inst.error_rate for inst in instances) / len(instances)
            
            return {
                'service_name': service_name,
                'instance_count': len(instances),
                'healthy_instances': healthy_count,
                'status': 'healthy' if healthy_count > 0 else 'unhealthy',
                'avg_response_time': avg_response_time,
                'avg_error_rate': avg_error_rate,
                'instances': [
                    {
                        'id': inst.id,
                        'url': inst.url,
                        'status': inst.status.value,
                        'response_time': inst.response_time,
                        'error_rate': inst.error_rate,
                        'active_connections': inst.active_connections
                    }
                    for inst in instances
                ]
            }

# Global service registry instance
service_registry = ServiceRegistry()

def initialize_default_routes():
    """
    Initialize default routing rules for Naebak platform services.
    
    This function sets up the standard routing configuration for all
    microservices in the Naebak platform with appropriate security
    and performance settings.
    """
    default_routes = [
        ("/api/auth/", RouteRule(
            pattern="/api/auth/",
            service_name="naebak-auth-service",
            auth_required=False,
            timeout=10,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )),
        ("/api/admin/", RouteRule(
            pattern="/api/admin/",
            service_name="naebak-admin-service",
            auth_required=True,
            admin_only=True,
            timeout=15,
            load_balancing=LoadBalancingStrategy.LEAST_CONNECTIONS
        )),
        ("/api/complaints/", RouteRule(
            pattern="/api/complaints/",
            service_name="naebak-complaints-service",
            auth_required=True,
            timeout=20,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )),
        ("/api/messages/", RouteRule(
            pattern="/api/messages/",
            service_name="naebak-messaging-service",
            auth_required=True,
            timeout=10,
            load_balancing=LoadBalancingStrategy.LEAST_CONNECTIONS
        )),
        ("/api/notifications/", RouteRule(
            pattern="/api/notifications/",
            service_name="naebak-notifications-service",
            auth_required=True,
            timeout=8,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )),
        ("/api/content/", RouteRule(
            pattern="/api/content/",
            service_name="naebak-content-service",
            auth_required=False,
            timeout=15,
            load_balancing=LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN
        )),
        ("/api/ratings/", RouteRule(
            pattern="/api/ratings/",
            service_name="naebak-ratings-service",
            auth_required=True,
            timeout=5,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )),
        ("/api/news/", RouteRule(
            pattern="/api/news/",
            service_name="naebak-news-service",
            auth_required=False,
            timeout=5,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )),
        ("/api/banners/", RouteRule(
            pattern="/api/banners/",
            service_name="naebak-banner-service",
            auth_required=False,
            timeout=10,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )),
        ("/api/visitors/", RouteRule(
            pattern="/api/visitors/",
            service_name="naebak-visitor-counter-service",
            auth_required=False,
            timeout=3,
            load_balancing=LoadBalancingStrategy.RANDOM
        )),
        ("/api/statistics/", RouteRule(
            pattern="/api/statistics/",
            service_name="naebak-statistics-service",
            auth_required=False,
            timeout=10,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )),
        ("/api/themes/", RouteRule(
            pattern="/api/themes/",
            service_name="naebak-theme-service",
            auth_required=True,
            timeout=5,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        ))
    ]
    
    for pattern, rule in default_routes:
        service_registry.add_route_rule(pattern, rule)
    
    logger.info(f"Initialized {len(default_routes)} default routing rules")

# Initialize default routes when module is imported
initialize_default_routes()
