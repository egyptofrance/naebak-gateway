"""
AI Governance Middleware

This middleware enforces AI governance policies on all requests
"""

import time
import json
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from .models import AIUsageQuota, AIAuditLog
from .utils.rate_limiter import RateLimiter
from .utils.quota_checker import QuotaChecker


class AIGovernanceMiddleware(MiddlewareMixin):
    """
    Middleware to enforce AI governance policies including:
    - Rate limiting
    - Quota enforcement
    - Request auditing
    - Security checks
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimiter()
        self.quota_checker = QuotaChecker()
        super().__init__(get_response)

    def process_request(self, request):
        """Process incoming requests for AI governance"""
        
        # Skip non-AI endpoints
        if not self._is_ai_endpoint(request.path):
            return None

        # Check if AI governance is enabled
        if not getattr(settings, 'AI_GOVERNANCE', {}).get('ENABLED', True):
            return None

        # Extract user information
        user = getattr(request, 'user', None)
        session_id = request.session.session_key
        ip_address = self._get_client_ip(request)

        # Rate limiting check
        if not self.rate_limiter.is_allowed(user, session_id, ip_address):
            self._log_governance_action(
                'quota_exceeded',
                f'Rate limit exceeded for {user or session_id or ip_address}',
                request,
                user
            )
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many AI requests. Please try again later.',
                'retry_after': self.rate_limiter.get_retry_after(user, session_id, ip_address)
            }, status=429)

        # Quota check
        quota_result = self.quota_checker.check_quota(user, session_id)
        if not quota_result['allowed']:
            self._log_governance_action(
                'quota_exceeded',
                f'Usage quota exceeded: {quota_result["reason"]}',
                request,
                user
            )
            return JsonResponse({
                'error': 'Quota exceeded',
                'message': quota_result['message'],
                'quota_reset': quota_result.get('reset_time')
            }, status=429)

        # Add governance context to request
        request.ai_governance = {
            'start_time': time.time(),
            'user': user,
            'session_id': session_id,
            'ip_address': ip_address,
            'quota_remaining': quota_result.get('remaining', {}),
        }

        return None

    def process_response(self, request, response):
        """Process responses for AI governance tracking"""
        
        # Skip non-AI endpoints
        if not self._is_ai_endpoint(request.path):
            return response

        # Skip if governance is disabled
        if not getattr(settings, 'AI_GOVERNANCE', {}).get('ENABLED', True):
            return response

        # Track response metrics
        if hasattr(request, 'ai_governance'):
            processing_time = time.time() - request.ai_governance['start_time']
            
            # Update rate limiter
            self.rate_limiter.record_request(
                request.ai_governance['user'],
                request.ai_governance['session_id'],
                request.ai_governance['ip_address'],
                processing_time
            )

            # Log successful request
            if response.status_code < 400:
                self._log_governance_action(
                    'request_completed',
                    f'AI request completed in {processing_time:.2f}s',
                    request,
                    request.ai_governance['user'],
                    {'processing_time': processing_time, 'status_code': response.status_code}
                )

        return response

    def _is_ai_endpoint(self, path):
        """Check if the request path is an AI-related endpoint"""
        ai_paths = [
            '/api/v1/ai-governance/',
            '/api/v1/chat/',
            '/api/v1/generate/',
            '/api/v1/analyze/',
        ]
        return any(path.startswith(ai_path) for ai_path in ai_paths)

    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _log_governance_action(self, action, description, request, user=None, metadata=None):
        """Log governance actions for auditing"""
        try:
            AIAuditLog.objects.create(
                action=action,
                description=description,
                user=user,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata=metadata or {}
            )
        except Exception as e:
            # Log error but don't break the request
            import logging
            logger = logging.getLogger('ai_governance')
            logger.error(f"Failed to log governance action: {e}")


class AIRequestValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate AI requests before processing
    """

    def process_request(self, request):
        """Validate AI requests"""
        
        if not self._is_ai_endpoint(request.path):
            return None

        # Validate request size
        if hasattr(request, 'body') and len(request.body) > 1024 * 1024:  # 1MB limit
            return JsonResponse({
                'error': 'Request too large',
                'message': 'Request body exceeds maximum allowed size'
            }, status=413)

        # Validate content type for POST requests
        if request.method == 'POST':
            content_type = request.content_type
            if content_type and not content_type.startswith('application/json'):
                return JsonResponse({
                    'error': 'Invalid content type',
                    'message': 'Only application/json is supported'
                }, status=415)

        return None

    def _is_ai_endpoint(self, path):
        """Check if the request path is an AI-related endpoint"""
        ai_paths = [
            '/api/v1/ai-governance/',
            '/api/v1/chat/',
            '/api/v1/generate/',
            '/api/v1/analyze/',
        ]
        return any(path.startswith(ai_path) for ai_path in ai_paths)
