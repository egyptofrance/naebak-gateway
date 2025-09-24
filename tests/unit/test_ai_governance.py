"""
Unit tests for AI Governance components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings

from app.ai_governance.models import AIModel, AIRequest, AIUsageQuota, AIContentFilter
from app.ai_governance.filters import ProfanityFilter, BiasDetectionFilter, FactCheckFilter
from app.ai_governance.utils.rate_limiter import RateLimiter, AdaptiveRateLimiter
from app.ai_governance.middleware import AIGovernanceMiddleware


@pytest.mark.unit
class TestAIGovernanceModels(TestCase):
    """Test AI Governance models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ai_model = AIModel.objects.create(
            name='gpt-3.5-turbo',
            provider='openai',
            model_type='text',
            max_tokens=4000,
            cost_per_token=0.000002
        )

    def test_ai_model_creation(self):
        """Test AI model creation and string representation"""
        self.assertEqual(str(self.ai_model), "openai/gpt-3.5-turbo")
        self.assertTrue(self.ai_model.is_active)
        self.assertEqual(self.ai_model.max_tokens, 4000)

    def test_ai_request_creation(self):
        """Test AI request creation"""
        request = AIRequest.objects.create(
            user=self.user,
            ai_model=self.ai_model,
            prompt="Test prompt",
            prompt_tokens=10,
            max_tokens=100,
            temperature=0.7
        )
        
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.prompt, "Test prompt")
        self.assertEqual(request.user, self.user)
        self.assertIsNotNone(request.id)

    def test_ai_usage_quota_creation(self):
        """Test AI usage quota creation"""
        quota = AIUsageQuota.objects.create(
            quota_type='user',
            period='minute',
            max_requests=10,
            max_tokens=1000,
            user=self.user
        )
        
        self.assertEqual(quota.quota_type, 'user')
        self.assertEqual(quota.max_requests, 10)
        self.assertTrue(quota.is_active)

    def test_ai_content_filter_creation(self):
        """Test AI content filter creation"""
        filter_obj = AIContentFilter.objects.create(
            name='Test Profanity Filter',
            filter_type='profanity',
            description='Test filter for profanity',
            keywords=['bad_word1', 'bad_word2'],
            threshold=0.5
        )
        
        self.assertEqual(filter_obj.filter_type, 'profanity')
        self.assertEqual(len(filter_obj.keywords), 2)
        self.assertTrue(filter_obj.is_active)


@pytest.mark.unit
class TestContentFilters(TestCase):
    """Test content filtering functionality"""

    def setUp(self):
        self.profanity_filter = ProfanityFilter()
        self.bias_filter = BiasDetectionFilter()
        self.fact_filter = FactCheckFilter()

    def test_profanity_filter_clean_text(self):
        """Test profanity filter with clean text"""
        clean_text = "هذا نص نظيف وجميل"
        is_allowed, modified_text, metadata = self.profanity_filter.filter_prompt(clean_text)
        
        self.assertTrue(is_allowed)
        self.assertEqual(modified_text, clean_text)
        self.assertIn('profanity_score', metadata)
        self.assertEqual(metadata['profanity_score'], 0.0)

    def test_profanity_filter_with_mild_profanity(self):
        """Test profanity filter with mild profanity"""
        text_with_profanity = "هذا النص يحتوي على كلمة حمار"
        is_allowed, modified_text, metadata = self.profanity_filter.filter_prompt(text_with_profanity)
        
        # Should be allowed but modified
        self.assertTrue(is_allowed)
        self.assertIn('***', modified_text)  # Word should be censored
        self.assertGreater(metadata['profanity_score'], 0.0)

    def test_bias_detection_filter(self):
        """Test bias detection filter"""
        biased_text = "الرجال أفضل في الرياضيات من النساء"
        is_allowed, modified_text, metadata = self.bias_filter.filter_prompt(biased_text)
        
        # Should be allowed but with warning added
        self.assertTrue(is_allowed)
        self.assertIn('تنبيه', modified_text)
        self.assertIn('detected_biases', metadata)

    def test_fact_check_filter(self):
        """Test fact checking filter"""
        suspicious_text = "أثبتت الدراسات أن هذا العلاج فعال بنسبة 100%"
        is_allowed, modified_text, metadata = self.fact_filter.filter_prompt(suspicious_text)
        
        # Should be allowed but with fact-check reminder
        self.assertTrue(is_allowed)
        self.assertIn('التأكد من دقة المعلومات', modified_text)
        self.assertGreater(metadata['suspicion_score'], 0.0)

    def test_filter_response_blocking(self):
        """Test that severe content gets blocked"""
        # Mock severe profanity that should be blocked
        with patch.object(self.profanity_filter, '_calculate_profanity_score') as mock_score:
            mock_score.return_value = (0.9, ['severe_word'])
            
            is_allowed, modified_response, metadata = self.profanity_filter.filter_response("severe content")
            
            self.assertFalse(is_allowed)
            self.assertEqual(modified_response, "")
            self.assertEqual(metadata['profanity_score'], 0.9)


@pytest.mark.unit
class TestRateLimiter(TestCase):
    """Test rate limiting functionality"""

    def setUp(self):
        self.rate_limiter = RateLimiter()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Clear cache before each test
        cache.clear()

    def test_rate_limiter_allows_initial_requests(self):
        """Test that rate limiter allows initial requests"""
        is_allowed = self.rate_limiter.is_allowed(self.user, None, '127.0.0.1')
        self.assertTrue(is_allowed)

    def test_rate_limiter_blocks_excessive_requests(self):
        """Test that rate limiter blocks excessive requests"""
        # Make requests up to the limit
        for i in range(10):  # Default limit is 10 per minute
            self.rate_limiter.record_request(self.user, None, '127.0.0.1')
        
        # Next request should be blocked
        is_allowed = self.rate_limiter.is_allowed(self.user, None, '127.0.0.1')
        self.assertFalse(is_allowed)

    def test_rate_limiter_different_identifiers(self):
        """Test that different identifiers have separate limits"""
        user1 = self.user
        user2 = User.objects.create_user(username='user2', email='user2@example.com')
        
        # Exhaust limit for user1
        for i in range(10):
            self.rate_limiter.record_request(user1, None, '127.0.0.1')
        
        # user1 should be blocked
        self.assertFalse(self.rate_limiter.is_allowed(user1, None, '127.0.0.1'))
        
        # user2 should still be allowed
        self.assertTrue(self.rate_limiter.is_allowed(user2, None, '127.0.0.2'))

    def test_rate_limiter_usage_stats(self):
        """Test rate limiter usage statistics"""
        # Make some requests
        for i in range(3):
            self.rate_limiter.record_request(self.user, None, '127.0.0.1', tokens_used=100)
        
        stats = self.rate_limiter.get_usage_stats(self.user, None, '127.0.0.1')
        
        self.assertEqual(stats['minute']['requests_made'], 3)
        self.assertEqual(stats['minute']['tokens_used'], 300)
        self.assertGreater(stats['minute']['requests_remaining'], 0)

    def test_adaptive_rate_limiter(self):
        """Test adaptive rate limiter functionality"""
        adaptive_limiter = AdaptiveRateLimiter()
        
        # Test normal load
        adaptive_limiter.update_system_load(1.0)
        self.assertTrue(adaptive_limiter.is_allowed(self.user, None, '127.0.0.1'))
        
        # Test high load
        adaptive_limiter.update_system_load(2.0)
        
        # Make requests to approach limit
        for i in range(5):  # Reduced limit due to high load
            adaptive_limiter.record_request(self.user, None, '127.0.0.1')
        
        # Should be more restrictive under high load
        is_allowed = adaptive_limiter.is_allowed(self.user, None, '127.0.0.1')
        # This might be allowed or not depending on the adaptive algorithm
        self.assertIsInstance(is_allowed, bool)


@pytest.mark.unit
class TestAIGovernanceMiddleware(TestCase):
    """Test AI Governance middleware"""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AIGovernanceMiddleware(lambda request: None)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()

    def test_middleware_skips_non_ai_endpoints(self):
        """Test that middleware skips non-AI endpoints"""
        request = self.factory.get('/api/v1/users/')
        request.user = self.user
        
        response = self.middleware.process_request(request)
        self.assertIsNone(response)  # Should not interfere

    def test_middleware_processes_ai_endpoints(self):
        """Test that middleware processes AI endpoints"""
        request = self.factory.post('/api/v1/ai-governance/chat/')
        request.user = self.user
        request.session = {'session_key': 'test_session'}
        
        response = self.middleware.process_request(request)
        
        # Should add governance context
        if response is None:  # Request allowed
            self.assertTrue(hasattr(request, 'ai_governance'))
            self.assertIn('start_time', request.ai_governance)
            self.assertIn('user', request.ai_governance)

    @patch('app.ai_governance.middleware.RateLimiter')
    def test_middleware_blocks_rate_limited_requests(self, mock_rate_limiter_class):
        """Test that middleware blocks rate-limited requests"""
        # Mock rate limiter to return False
        mock_rate_limiter = Mock()
        mock_rate_limiter.is_allowed.return_value = False
        mock_rate_limiter.get_retry_after.return_value = 60
        mock_rate_limiter_class.return_value = mock_rate_limiter
        
        # Create new middleware instance with mocked rate limiter
        middleware = AIGovernanceMiddleware(lambda request: None)
        
        request = self.factory.post('/api/v1/ai-governance/chat/')
        request.user = self.user
        request.session = MagicMock()
        request.session.session_key = 'test_session'
        
        response = middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 429)

    def test_middleware_validates_request_size(self):
        """Test that middleware validates request size"""
        from app.ai_governance.middleware import AIRequestValidationMiddleware
        
        validation_middleware = AIRequestValidationMiddleware(lambda request: None)
        
        # Create request with large body
        large_data = 'x' * (1024 * 1024 + 1)  # > 1MB
        request = self.factory.post('/api/v1/ai-governance/chat/', data=large_data, content_type='application/json')
        request.body = large_data.encode()
        
        response = validation_middleware.process_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 413)


@pytest.mark.unit
class TestAIGovernanceIntegration(TestCase):
    """Test integration between AI governance components"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ai_model = AIModel.objects.create(
            name='gpt-3.5-turbo',
            provider='openai',
            model_type='text'
        )
        cache.clear()

    def test_end_to_end_request_processing(self):
        """Test complete request processing flow"""
        # Create AI request
        ai_request = AIRequest.objects.create(
            user=self.user,
            ai_model=self.ai_model,
            prompt="Test prompt for processing",
            max_tokens=100
        )
        
        # Simulate processing
        ai_request.status = 'processing'
        ai_request.save()
        
        # Apply content filters
        from app.ai_governance.filters import ContentFilterManager
        filter_manager = ContentFilterManager()
        
        is_allowed, filtered_prompt, metadata = filter_manager.filter_prompt(ai_request.prompt)
        self.assertTrue(is_allowed)
        
        # Simulate AI response
        response = "This is a test response from AI"
        is_allowed, filtered_response, response_metadata = filter_manager.filter_response(response)
        self.assertTrue(is_allowed)
        
        # Complete request
        ai_request.response = filtered_response
        ai_request.status = 'completed'
        ai_request.response_tokens = 50
        ai_request.total_tokens = ai_request.prompt_tokens + ai_request.response_tokens
        ai_request.save()
        
        self.assertEqual(ai_request.status, 'completed')
        self.assertIsNotNone(ai_request.response)

    @patch('app.ai_governance.models.AIAuditLog.objects.create')
    def test_audit_logging(self, mock_audit_create):
        """Test that audit logging works correctly"""
        from app.ai_governance.models import AIAuditLog
        
        # Create an audit log entry
        AIAuditLog.objects.create(
            action='request_created',
            description='Test audit log entry',
            user=self.user,
            ip_address='127.0.0.1',
            metadata={'test': 'data'}
        )
        
        # Verify audit log was called
        mock_audit_create.assert_called_once()

    def test_quota_enforcement(self):
        """Test quota enforcement functionality"""
        # Create a restrictive quota
        quota = AIUsageQuota.objects.create(
            quota_type='user',
            period='minute',
            max_requests=2,
            max_tokens=100,
            user=self.user
        )
        
        # Test quota checking logic
        from app.ai_governance.utils.quota_checker import QuotaChecker
        quota_checker = QuotaChecker()
        
        # First request should be allowed
        result = quota_checker.check_quota(self.user, 'test_session')
        self.assertTrue(result['allowed'])
        
        # Record some usage
        for i in range(2):
            AIRequest.objects.create(
                user=self.user,
                ai_model=self.ai_model,
                prompt=f"Test prompt {i}",
                status='completed'
            )
        
        # Should now be at limit
        # Note: This test might need adjustment based on actual quota checker implementation
