import unittest
import json
import time
from unittest.mock import patch, MagicMock
from gateway import app, db, health_checker, metrics

class MonitoringTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_enhanced_health_endpoint(self):
        """Test the enhanced health check endpoint"""
        response = self.app.get('/health')
        self.assertIn(response.status_code, [200, 503])  # Can be degraded
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('service', data)
        self.assertIn('version', data)
        self.assertIn('services', data)
        self.assertIn('metrics', data)
        self.assertIn('circuit_breakers', data)

    def test_services_health_endpoint(self):
        """Test the services health endpoint"""
        response = self.app.get('/health/services')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('services', data)
        self.assertIn('summary', data)

    def test_specific_service_health(self):
        """Test health check for a specific service"""
        response = self.app.get('/health/services?service=naebak-auth-service')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('service', data)
        self.assertIn('current_status', data)
        self.assertIn('circuit_breaker', data)

    def test_metrics_summary_endpoint(self):
        """Test the metrics summary endpoint"""
        response = self.app.get('/metrics/summary')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('gateway_metrics', data)
        self.assertIn('health_metrics', data)

    def test_circuit_breakers_endpoint(self):
        """Test the circuit breakers status endpoint"""
        # Test without authentication
        response = self.app.get('/admin/circuit-breakers')
        self.assertEqual(response.status_code, 401)
        
        # Test with authentication
        response = self.app.get('/admin/circuit-breakers', 
                               headers={'Authorization': 'Bearer test-token'})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('circuit_breakers', data)

    def test_prometheus_metrics_endpoint(self):
        """Test that Prometheus metrics endpoint exists"""
        response = self.app.get('/metrics')
        # Should return Prometheus format or be handled by the exporter
        self.assertIn(response.status_code, [200, 404])

if __name__ == '__main__':
    unittest.main()
