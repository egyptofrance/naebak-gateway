import unittest
import json
from unittest.mock import patch, MagicMock
from gateway import app, db

class GatewayIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('requests.request')
    def test_auth_service_integration(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": "Auth Success"}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_request.return_value = mock_response

        response = self.app.get('/api/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'{"message": "Auth Success"}')

    @patch('requests.request')
    def test_admin_service_integration(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": "Admin Success"}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_request.return_value = mock_response

        # This request would normally require admin authentication
        # For this test, we are just checking the routing and response proxying
        response = self.app.get('/api/admin/users', headers={'Authorization': 'Bearer admin-token'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'{"message": "Admin Success"}')

if __name__ == '__main__':
    unittest.main()

