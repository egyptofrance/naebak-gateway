import unittest
import json
from unittest.mock import patch, MagicMock
from gateway import app, db

class GatewayTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_list_services(self):
        response = self.app.get('/api/gateway/services')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('services', data['data'])

    @patch('requests.request')
    def test_proxy_request_success(self, mock_request):
        # Mock the response from the downstream service
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": "Success"}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_request.return_value = mock_response

        response = self.app.get('/api/content/some/path')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'{"message": "Success"}')

    def test_proxy_request_no_service_found(self):
        response = self.app.get('/api/nonexistent/path')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'SERVICE_NOT_FOUND')

if __name__ == '__main__':
    unittest.main()
