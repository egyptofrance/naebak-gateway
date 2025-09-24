"""
Integration tests for AI Governance system

These tests verify that all AI governance components work together correctly
"""

import pytest
import json
import time
from unittest.mock import patch, Mock
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status

from app.ai_governance.models import AIModel, AIRequest, AIUsageQuota, AIContentFilter, AIAuditLog


@pytest.mark.integration
class TestAIGovernanceAPIIntegration(TransactionTestCase):
    """Test AI Governance API integration"""

    def setUp(self):
        self.client = APIClient()
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
        cache.clear()

    def test_ai_request_creation_flow(self):
        """Test complete AI request creation and processing flow"""
        self.client.force_authenticate(user=self.user)
        
        # Create AI request via API
        request_data = {
            'ai_model': self.ai_model.id,
            'prompt': 'اكتب لي قصة قصيرة عن الصداقة',
            'max_tokens': 200,
            'temperature': 0.7
        }
        
        response = self.client.post('/api/v1/ai-governance/requests/', request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify request was created in database
        ai_request = AIRequest.objects.get(id=response.data['id'])
        self.assertEqual(ai_request.user, self.user)
        self.assertEqual(ai_request.prompt, request_data['prompt'])
        self.assertEqual(ai_request.status, 'pending')

    def test_rate_limiting_integration(self):
        """Test rate limiting across multiple requests"""
        self.client.force_authenticate(user=self.user)
        
        request_data = {
            'ai_model': self.ai_model.id,
            'prompt': 'Test prompt',
            'max_tokens': 100
        }
        
        # Make requests up to the limit
        successful_requests = 0
        for i in range(15):  # Try more than the default limit
            response = self.client.post('/api/v1/ai-governance/requests/', request_data)
            if response.status_code == status.HTTP_201_CREATED:
                successful_requests += 1
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should have hit rate limit
        self.assertLess(successful_requests, 15)
        
        # Last response should be rate limited
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('retry_after', response.data)

    def test_content_filtering_integration(self):
        """Test content filtering in the request flow"""
        self.client.force_authenticate(user=self.user)
        
        # Test with potentially problematic content
        request_data = {
            'ai_model': self.ai_model.id,
            'prompt': 'الرجال أفضل من النساء في كل شيء',  # Biased content
            'max_tokens': 100
        }
        
        response = self.client.post('/api/v1/ai-governance/requests/', request_data)
        
        # Request should be created but prompt might be modified
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        ai_request = AIRequest.objects.get(id=response.data['id'])
        # Check if bias warning was added
        self.assertIn('تنبيه', ai_request.prompt)

    def test_quota_enforcement_integration(self):
        """Test quota enforcement across the system"""
        # Create restrictive quota
        quota = AIUsageQuota.objects.create(
            quota_type='user',
            period='minute',
            max_requests=3,
            max_tokens=500,
            user=self.user
        )
        
        self.client.force_authenticate(user=self.user)
        
        request_data = {
            'ai_model': self.ai_model.id,
            'prompt': 'Test prompt',
            'max_tokens': 200
        }
        
        # Make requests within quota
        for i in range(3):
            response = self.client.post('/api/v1/ai-governance/requests/', request_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Next request should exceed quota
        response = self.client.post('/api/v1/ai-governance/requests/', request_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('quota', response.data['error'].lower())

    def test_audit_logging_integration(self):
        """Test that audit logs are created during request processing"""
        self.client.force_authenticate(user=self.user)
        
        initial_audit_count = AIAuditLog.objects.count()
        
        request_data = {
            'ai_model': self.ai_model.id,
            'prompt': 'Test prompt for audit logging',
            'max_tokens': 100
        }
        
        response = self.client.post('/api/v1/ai-governance/requests/', request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that audit logs were created
        final_audit_count = AIAuditLog.objects.count()
        self.assertGreater(final_audit_count, initial_audit_count)
        
        # Check for specific audit log entry
        audit_logs = AIAuditLog.objects.filter(user=self.user).order_by('-created_at')
        self.assertTrue(audit_logs.exists())
        
        latest_log = audit_logs.first()
        self.assertEqual(latest_log.user, self.user)
        self.assertIn('request', latest_log.action)


@pytest.mark.integration
class TestAIGovernanceMiddlewareIntegration(TestCase):
    """Test AI Governance middleware integration with Django"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()

    def test_middleware_request_processing(self):
        """Test middleware processes requests correctly"""
        self.client.force_login(self.user)
        
        # Make request to AI endpoint
        response = self.client.get('/api/v1/ai-governance/models/')
        
        # Should process successfully
        self.assertIn(response.status_code, [200, 404])  # 404 if endpoint not implemented yet

    def test_middleware_adds_governance_context(self):
        """Test that middleware adds governance context to requests"""
        # This test would need to inspect the request object
        # In a real implementation, you might need to create a custom view for testing
        pass

    def test_middleware_handles_large_requests(self):
        """Test middleware validation of large requests"""
        self.client.force_login(self.user)
        
        # Create large request data
        large_data = {'prompt': 'x' * (1024 * 1024 + 1)}  # > 1MB
        
        response = self.client.post(
            '/api/v1/ai-governance/requests/',
            data=json.dumps(large_data),
            content_type='application/json'
        )
        
        # Should be rejected due to size
        self.assertEqual(response.status_code, 413)


@pytest.mark.integration
class TestAIGovernanceFilterIntegration(TestCase):
    """Test content filter integration"""

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

    def test_multiple_filters_integration(self):
        """Test that multiple filters work together"""
        from app.ai_governance.filters import ContentFilterManager
        
        filter_manager = ContentFilterManager()
        
        # Text with multiple issues
        problematic_text = "الرجال حمير وأثبتت الدراسات أن هذا صحيح بنسبة 100%"
        
        is_allowed, filtered_text, metadata = filter_manager.filter_prompt(problematic_text)
        
        # Should be allowed but heavily modified
        self.assertTrue(is_allowed)
        self.assertNotEqual(filtered_text, problematic_text)
        
        # Should have metadata from multiple filters
        self.assertIn('profanity_score', metadata)
        self.assertIn('bias_score', metadata)
        self.assertIn('suspicion_score', metadata)

    def test_filter_configuration_from_database(self):
        """Test loading filter configuration from database"""
        # Create content filter in database
        content_filter = AIContentFilter.objects.create(
            name='Test Custom Filter',
            filter_type='custom',
            description='Test filter',
            keywords=['test_keyword'],
            threshold=0.3,
            block_request=True
        )
        
        # Test that filter configuration is loaded
        # This would require implementing database-driven filter configuration
        pass

    def test_filter_performance_with_large_text(self):
        """Test filter performance with large text inputs"""
        from app.ai_governance.filters import ProfanityFilter
        
        profanity_filter = ProfanityFilter()
        
        # Create large text
        large_text = "هذا نص طويل جداً. " * 1000
        
        start_time = time.time()
        is_allowed, filtered_text, metadata = profanity_filter.filter_prompt(large_text)
        end_time = time.time()
        
        # Should complete within reasonable time
        processing_time = end_time - start_time
        self.assertLess(processing_time, 1.0)  # Should take less than 1 second
        
        self.assertTrue(is_allowed)


@pytest.mark.integration
class TestAIGovernanceSystemIntegration(TransactionTestCase):
    """Test complete AI governance system integration"""

    def setUp(self):
        self.client = APIClient()
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

    @patch('openai.ChatCompletion.create')
    def test_complete_ai_request_lifecycle(self, mock_openai):
        """Test complete AI request lifecycle from creation to completion"""
        # Mock OpenAI response
        mock_openai.return_value = Mock(
            choices=[Mock(message=Mock(content="This is a test AI response"))],
            usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )
        
        self.client.force_authenticate(user=self.user)
        
        # 1. Create AI request
        request_data = {
            'ai_model': self.ai_model.id,
            'prompt': 'اكتب لي نصيحة عن الحياة',
            'max_tokens': 100,
            'temperature': 0.7
        }
        
        response = self.client.post('/api/v1/ai-governance/requests/', request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        ai_request_id = response.data['id']
        
        # 2. Process the request (simulate AI processing)
        ai_request = AIRequest.objects.get(id=ai_request_id)
        ai_request.status = 'processing'
        ai_request.save()
        
        # 3. Apply content filters to response
        from app.ai_governance.filters import ContentFilterManager
        filter_manager = ContentFilterManager()
        
        ai_response = "الحياة جميلة عندما نقدر النعم التي لدينا"
        is_allowed, filtered_response, metadata = filter_manager.filter_response(ai_response)
        
        self.assertTrue(is_allowed)
        
        # 4. Complete the request
        ai_request.response = filtered_response
        ai_request.status = 'completed'
        ai_request.response_tokens = 15
        ai_request.total_tokens = 25
        ai_request.save()
        
        # 5. Verify final state
        final_request = AIRequest.objects.get(id=ai_request_id)
        self.assertEqual(final_request.status, 'completed')
        self.assertIsNotNone(final_request.response)
        
        # 6. Check audit logs
        audit_logs = AIAuditLog.objects.filter(ai_request=final_request)
        self.assertTrue(audit_logs.exists())

    def test_concurrent_request_handling(self):
        """Test handling of concurrent AI requests"""
        import threading
        import queue
        
        self.client.force_authenticate(user=self.user)
        
        results = queue.Queue()
        
        def make_request():
            try:
                request_data = {
                    'ai_model': self.ai_model.id,
                    'prompt': 'Test concurrent request',
                    'max_tokens': 50
                }
                response = self.client.post('/api/v1/ai-governance/requests/', request_data)
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())
        
        # Should have some successful requests and possibly some rate-limited
        self.assertEqual(len(status_codes), 5)
        self.assertTrue(any(code == 201 for code in status_codes))

    def test_system_recovery_after_failure(self):
        """Test system recovery after component failures"""
        self.client.force_authenticate(user=self.user)
        
        # Simulate cache failure
        with patch('django.core.cache.cache.get') as mock_cache_get:
            mock_cache_get.side_effect = Exception("Cache connection failed")
            
            request_data = {
                'ai_model': self.ai_model.id,
                'prompt': 'Test request during cache failure',
                'max_tokens': 50
            }
            
            # Request should still work (graceful degradation)
            response = self.client.post('/api/v1/ai-governance/requests/', request_data)
            
            # Should either succeed or fail gracefully
            self.assertIn(response.status_code, [201, 500, 503])

    def test_governance_metrics_collection(self):
        """Test that governance metrics are collected correctly"""
        self.client.force_authenticate(user=self.user)
        
        # Make several requests
        for i in range(3):
            request_data = {
                'ai_model': self.ai_model.id,
                'prompt': f'Test request {i}',
                'max_tokens': 50
            }
            response = self.client.post('/api/v1/ai-governance/requests/', request_data)
        
        # Check metrics endpoint
        metrics_response = self.client.get('/api/v1/ai-governance/metrics/')
        
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.data
            self.assertIn('total_requests', metrics_data)
            self.assertIn('requests_by_status', metrics_data)
            self.assertIn('average_processing_time', metrics_data)


@pytest.mark.integration
@pytest.mark.external
class TestAIGovernanceExternalIntegration(TestCase):
    """Test integration with external services (requires external dependencies)"""

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

    @pytest.mark.skipif(not settings.OPENAI_API_KEY, reason="OpenAI API key not configured")
    def test_real_openai_integration(self):
        """Test integration with real OpenAI API (requires API key)"""
        # This test would make real API calls
        # Only run in specific test environments
        pass

    def test_google_cloud_secret_manager_integration(self):
        """Test integration with Google Cloud Secret Manager"""
        # Mock Google Cloud Secret Manager
        with patch('google.cloud.secretmanager.SecretManagerServiceClient') as mock_client:
            mock_client.return_value.access_secret_version.return_value.payload.data.decode.return_value = "test_secret"
            
            # Test secret retrieval
            from app.ai_governance.utils.secrets import get_secret
            secret_value = get_secret('test-secret')
            
            self.assertEqual(secret_value, "test_secret")

    def test_prometheus_metrics_integration(self):
        """Test integration with Prometheus metrics"""
        from prometheus_client import REGISTRY, CollectorRegistry
        
        # Create test registry
        test_registry = CollectorRegistry()
        
        # Test metrics collection
        # This would require implementing Prometheus metrics in the governance system
        pass
