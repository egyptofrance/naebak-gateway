
import unittest
from unittest.mock import Mock
from app import app
from utils.load_balancer import LoadBalancer

class TestUtils(unittest.TestCase):

    def test_load_balancer(self):
        urls = ["http://service1", "http://service2", "http://service3"]
        lb = LoadBalancer(urls)
        
        # Test round-robin behavior
        self.assertEqual(lb.get_next_service_url(), "http://service1")
        self.assertEqual(lb.get_next_service_url(), "http://service2")
        self.assertEqual(lb.get_next_service_url(), "http://service3")
        self.assertEqual(lb.get_next_service_url(), "http://service1")

if __name__ == "__main__":
    unittest.main()

