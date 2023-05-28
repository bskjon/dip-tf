import unittest
from unittest.mock import patch
from subprocess import CompletedProcess
from DynamicRoutingUpdater.objects import Route, IpData
from DynamicRoutingUpdater.Routing import Routing

class MockCompletedProcess(CompletedProcess):
    def __init__(self, returncode, stdout):
        self.returncode = returncode
        self.stdout = stdout

class TestRouting(unittest.TestCase):
    @patch('DynamicRoutingUpdater.Routing.subprocess.getoutput')
    def test_getRoutes(self, mock_getoutput):
        # Set up mock return value for subprocess.getoutput
        mock_getoutput.return_value = '[{"dst": "192.168.0.0/24", "gateway": "192.168.1.1", "dev": "eth0", "prefsrc": "192.168.0.2", "scope": "link"}]'
        
        expected_routes = [
            Route("192.168.0.0/24", "192.168.1.1", "eth0", "192.168.0.2", "link")
        ]
        
        # Create an instance of Routing and call getRoutes
        routing = Routing("default")
        routes = routing.getRoutes()
        
        
        print("===Result====")
        print("\n".join([str(obj) for obj in routes])) 

        print("\n===Excpected===")
        print("\n".join([str(obj) for obj in expected_routes])) 
        
        # Assert that the returned routes match the expected routes
        self.assertListEqual(
            [r.__dict__ for r in routes],
            [r.__dict__ for r in expected_routes]
        )
    

if __name__ == '__main__':
    unittest.main()
