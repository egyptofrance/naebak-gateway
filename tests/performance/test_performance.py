import unittest
import time
from unittest.mock import patch, MagicMock
from gateway import app, db

class GatewayPerformanceTest(unittest.TestCase):
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
    def test_load_performance(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"message": "Success"}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_request.return_value = mock_response

        start_time = time.time()
        for _ in range(100):
            self.app.get('/api/content/some/path')
        end_time = time.time()

        duration = end_time - start_time
        print(f"\n100 requests took {duration:.4f} seconds")
        self.assertLess(duration, 5)  # Assert that 100 requests take less than 5 seconds

if __name__ == '__main__':
    unittest.main()

