"""
Rate Limiter for AI Governance

Implements sophisticated rate limiting with multiple strategies
"""

import time
import json
from typing import Optional, Dict, Any, Union
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
import logging

logger = logging.getLogger('ai_governance')


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies:
    - Token bucket algorithm
    - Sliding window
    - User-based and IP-based limiting
    """
    
    def __init__(self):
        self.config = getattr(settings, 'AI_GOVERNANCE', {})
        self.default_limits = {
            'requests_per_minute': self.config.get('MAX_REQUESTS_PER_MINUTE', 10),
            'requests_per_hour': 100,
            'requests_per_day': 1000,
            'tokens_per_minute': 10000,
            'tokens_per_hour': 100000,
        }
        self.cache_timeout = 3600  # 1 hour

    def is_allowed(self, user: Optional[User], session_id: Optional[str], ip_address: str) -> bool:
        """
        Check if request is allowed based on rate limits
        """
        # Get identifier for rate limiting
        identifier = self._get_identifier(user, session_id, ip_address)
        
        # Check different rate limit windows
        checks = [
            self._check_minute_limit(identifier),
            self._check_hour_limit(identifier),
            self._check_day_limit(identifier),
        ]
        
        # All checks must pass
        return all(checks)

    def record_request(self, user: Optional[User], session_id: Optional[str], 
                      ip_address: str, processing_time: float = 0.0, tokens_used: int = 0):
        """
        Record a request for rate limiting tracking
        """
        identifier = self._get_identifier(user, session_id, ip_address)
        current_time = time.time()
        
        # Record in different time windows
        self._record_in_window(identifier, 'minute', current_time, tokens_used)
        self._record_in_window(identifier, 'hour', current_time, tokens_used)
        self._record_in_window(identifier, 'day', current_time, tokens_used)
        
        # Record processing time for adaptive limiting
        self._record_processing_time(identifier, processing_time)

    def get_retry_after(self, user: Optional[User], session_id: Optional[str], ip_address: str) -> int:
        """
        Get the number of seconds to wait before retrying
        """
        identifier = self._get_identifier(user, session_id, ip_address)
        
        # Check which limit was exceeded and return appropriate retry time
        if not self._check_minute_limit(identifier):
            return 60  # Wait 1 minute
        elif not self._check_hour_limit(identifier):
            return 3600  # Wait 1 hour
        elif not self._check_day_limit(identifier):
            return 86400  # Wait 1 day
        
        return 60  # Default

    def get_usage_stats(self, user: Optional[User], session_id: Optional[str], ip_address: str) -> Dict[str, Any]:
        """
        Get current usage statistics for the identifier
        """
        identifier = self._get_identifier(user, session_id, ip_address)
        
        return {
            'minute': self._get_window_stats(identifier, 'minute'),
            'hour': self._get_window_stats(identifier, 'hour'),
            'day': self._get_window_stats(identifier, 'day'),
            'limits': self._get_limits_for_identifier(identifier),
        }

    def _get_identifier(self, user: Optional[User], session_id: Optional[str], ip_address: str) -> str:
        """
        Get unique identifier for rate limiting
        Priority: user_id > session_id > ip_address
        """
        if user and user.is_authenticated:
            return f"user:{user.id}"
        elif session_id:
            return f"session:{session_id}"
        else:
            return f"ip:{ip_address}"

    def _check_minute_limit(self, identifier: str) -> bool:
        """Check minute-based rate limit"""
        return self._check_window_limit(identifier, 'minute', 60, 
                                      self._get_limits_for_identifier(identifier)['requests_per_minute'])

    def _check_hour_limit(self, identifier: str) -> bool:
        """Check hour-based rate limit"""
        return self._check_window_limit(identifier, 'hour', 3600, 
                                      self._get_limits_for_identifier(identifier)['requests_per_hour'])

    def _check_day_limit(self, identifier: str) -> bool:
        """Check day-based rate limit"""
        return self._check_window_limit(identifier, 'day', 86400, 
                                      self._get_limits_for_identifier(identifier)['requests_per_day'])

    def _check_window_limit(self, identifier: str, window: str, window_seconds: int, limit: int) -> bool:
        """
        Check rate limit for a specific time window using sliding window algorithm
        """
        cache_key = f"rate_limit:{identifier}:{window}"
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Get existing requests in this window
        requests = cache.get(cache_key, [])
        
        # Filter requests within the current window
        valid_requests = [req_time for req_time in requests if req_time > window_start]
        
        # Check if under limit
        return len(valid_requests) < limit

    def _record_in_window(self, identifier: str, window: str, timestamp: float, tokens_used: int = 0):
        """
        Record a request in the specified time window
        """
        cache_key = f"rate_limit:{identifier}:{window}"
        
        # Get existing requests
        requests = cache.get(cache_key, [])
        
        # Add new request
        requests.append(timestamp)
        
        # Clean old requests based on window
        window_seconds = {'minute': 60, 'hour': 3600, 'day': 86400}[window]
        cutoff_time = timestamp - window_seconds
        requests = [req_time for req_time in requests if req_time > cutoff_time]
        
        # Store back in cache
        cache.set(cache_key, requests, self.cache_timeout)
        
        # Record tokens if provided
        if tokens_used > 0:
            self._record_tokens(identifier, window, tokens_used, timestamp)

    def _record_tokens(self, identifier: str, window: str, tokens_used: int, timestamp: float):
        """
        Record token usage for the identifier
        """
        cache_key = f"tokens:{identifier}:{window}"
        
        # Get existing token usage
        token_data = cache.get(cache_key, {'total': 0, 'requests': []})
        
        # Add new token usage
        token_data['total'] += tokens_used
        token_data['requests'].append({'timestamp': timestamp, 'tokens': tokens_used})
        
        # Clean old requests
        window_seconds = {'minute': 60, 'hour': 3600, 'day': 86400}[window]
        cutoff_time = timestamp - window_seconds
        
        valid_requests = [req for req in token_data['requests'] if req['timestamp'] > cutoff_time]
        token_data['requests'] = valid_requests
        token_data['total'] = sum(req['tokens'] for req in valid_requests)
        
        # Store back in cache
        cache.set(cache_key, token_data, self.cache_timeout)

    def _record_processing_time(self, identifier: str, processing_time: float):
        """
        Record processing time for adaptive rate limiting
        """
        cache_key = f"processing_time:{identifier}"
        
        # Get existing processing times (keep last 10)
        times = cache.get(cache_key, [])
        times.append(processing_time)
        
        # Keep only last 10 processing times
        if len(times) > 10:
            times = times[-10:]
        
        cache.set(cache_key, times, self.cache_timeout)

    def _get_window_stats(self, identifier: str, window: str) -> Dict[str, Any]:
        """
        Get statistics for a specific time window
        """
        cache_key = f"rate_limit:{identifier}:{window}"
        requests = cache.get(cache_key, [])
        
        token_cache_key = f"tokens:{identifier}:{window}"
        token_data = cache.get(token_cache_key, {'total': 0, 'requests': []})
        
        limits = self._get_limits_for_identifier(identifier)
        limit_key = f"requests_per_{window}"
        
        return {
            'requests_made': len(requests),
            'requests_limit': limits.get(limit_key, 0),
            'requests_remaining': max(0, limits.get(limit_key, 0) - len(requests)),
            'tokens_used': token_data['total'],
            'tokens_limit': limits.get(f"tokens_per_{window}", 0),
        }

    def _get_limits_for_identifier(self, identifier: str) -> Dict[str, int]:
        """
        Get rate limits for a specific identifier
        Can be customized based on user type, subscription, etc.
        """
        # Default limits
        limits = self.default_limits.copy()
        
        # Customize based on identifier type
        if identifier.startswith('user:'):
            user_id = identifier.split(':')[1]
            # Here you could load user-specific limits from database
            # For now, use default limits
            pass
        elif identifier.startswith('session:'):
            # Session-based limits (might be more restrictive)
            limits['requests_per_minute'] = max(1, limits['requests_per_minute'] // 2)
        elif identifier.startswith('ip:'):
            # IP-based limits (most restrictive)
            limits['requests_per_minute'] = max(1, limits['requests_per_minute'] // 4)
        
        return limits


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts limits based on system load and user behavior
    """
    
    def __init__(self):
        super().__init__()
        self.load_factor = 1.0  # System load factor (1.0 = normal, >1.0 = high load)

    def is_allowed(self, user: Optional[User], session_id: Optional[str], ip_address: str) -> bool:
        """
        Check if request is allowed with adaptive limits
        """
        # Get base allowance
        base_allowed = super().is_allowed(user, session_id, ip_address)
        
        if not base_allowed:
            return False
        
        # Apply adaptive logic
        identifier = self._get_identifier(user, session_id, ip_address)
        
        # Check system load
        if self.load_factor > 1.5:
            # High system load - be more restrictive
            return self._check_adaptive_limit(identifier)
        
        # Check user behavior patterns
        if self._is_suspicious_behavior(identifier):
            return False
        
        return True

    def _check_adaptive_limit(self, identifier: str) -> bool:
        """
        Apply adaptive limits based on system load
        """
        # Reduce limits based on load factor
        adjusted_limit = int(self.default_limits['requests_per_minute'] / self.load_factor)
        
        cache_key = f"rate_limit:{identifier}:minute"
        current_time = time.time()
        window_start = current_time - 60
        
        requests = cache.get(cache_key, [])
        valid_requests = [req_time for req_time in requests if req_time > window_start]
        
        return len(valid_requests) < adjusted_limit

    def _is_suspicious_behavior(self, identifier: str) -> bool:
        """
        Detect suspicious behavior patterns
        """
        # Check for rapid-fire requests
        cache_key = f"rate_limit:{identifier}:minute"
        requests = cache.get(cache_key, [])
        
        if len(requests) >= 2:
            # Check if last two requests were too close together
            time_diff = requests[-1] - requests[-2]
            if time_diff < 1.0:  # Less than 1 second apart
                logger.warning(f"Suspicious rapid requests detected for {identifier}")
                return True
        
        # Check processing time patterns
        processing_cache_key = f"processing_time:{identifier}"
        processing_times = cache.get(processing_cache_key, [])
        
        if len(processing_times) >= 5:
            avg_time = sum(processing_times) / len(processing_times)
            if avg_time > 10.0:  # Average processing time > 10 seconds
                # User might be making complex requests too frequently
                return True
        
        return False

    def update_system_load(self, load_factor: float):
        """
        Update system load factor for adaptive limiting
        """
        self.load_factor = max(0.1, min(5.0, load_factor))  # Clamp between 0.1 and 5.0
        logger.info(f"System load factor updated to {self.load_factor}")
