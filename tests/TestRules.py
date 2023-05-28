import unittest
from unittest.mock import patch
import subprocess
import json
from DynamicRoutingUpdater.objects import Rule, IpData
from DynamicRoutingUpdater.Rules import Rules

class MockCompletedProcess(subprocess.CompletedProcess):
    def __init__(self, returncode, stdout):
        self.returncode = returncode
        self.stdout = stdout

class TestRules(unittest.TestCase):
    @patch('DynamicRoutingUpdater.Rules.subprocess.getoutput')
    def test_getRules(self, mock_getoutput):
        # Set up mock return value for subprocess.getoutput
        mock_getoutput.return_value = '[{"priority": 100, "src": "192.168.0.0/24", "table": "main"}]'
        
        expected_rules = [
            Rule(100, "192.168.0.0/24", "main")
        ]
        
        # Create an instance of Rules and call getRules
        rules = Rules()
        result = rules.getRules()
        
        # Assert that the returned rules match the expected rules
        self.assertEqual(len(result), len(expected_rules))
        self.assertListEqual(
            [r.__dict__ for r in result],
            [r.__dict__ for r in expected_rules])
    
#    @patch('DynamicRoutingUpdater.Rules.subprocess.os.system')
#    def test_addRule(self, mock_os_system):
#        rules = Rules()
#        source = "192.168.0.0/24"
#        table = "main"
#        expected_command = f"ip rule add from {source} table {table}"
#        
#        # Call addRule method
#        rules.addRule(source, table)
#        
#        # Assert that os.system was called with the expected command
#        mock_os_system.assert_called_once_with(expected_command)
#    
#    @patch('DynamicRoutingUpdater.Rules.subprocess.os.system')
#    def test_deleteRule(self, mock_os_system):
#        rules = Rules()
#        table = "main"
#        expected_command = f"ip rule del table {table}"
#        
#        # Call deleteRule method
#        rules.deleteRule(table)
#        
#        # Assert that os.system was called with the expected command
#        mock_os_system.assert_called_once_with(expected_command)

if __name__ == '__main__':
    unittest.main()
