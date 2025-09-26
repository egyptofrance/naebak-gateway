import unittest
import json
from unittest.mock import patch, MagicMock
from gateway import app, db

class GatewaySecurityTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_missing_auth_header(self):
        response = self.app.get("/api/admin/users")
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data["error"]["code"], "AUTHENTICATION_FAILED")

    def test_invalid_auth_header(self):
        response = self.app.get("/api/admin/users", headers={"Authorization": "Invalid token"})
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data["error"]["code"], "AUTHENTICATION_FAILED")

    @patch("gateway.verify_jwt_token")
    def test_admin_access_denied(self, mock_verify_jwt):
        mock_verify_jwt.return_value = {"user_id": 1, "is_admin": False}
        response = self.app.get("/api/admin/users", headers={"Authorization": "Bearer user-token"})
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data["error"]["message"], "Admin privileges required")

    @patch("gateway.verify_jwt_token")
    @patch("requests.request")
    def test_admin_access_granted(self, mock_request, mock_verify_jwt):
        mock_verify_jwt.return_value = {"user_id": 1, "is_admin": True}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": "Admin access granted"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response

        response = self.app.get("/api/admin/users", headers={"Authorization": "Bearer admin-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'{"message": "Admin access granted"}')

if __name__ == "__main__":
    unittest.main()

