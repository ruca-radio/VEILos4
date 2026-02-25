"""
VEILos Test Suite
=================
Comprehensive tests for VEILos pseudo-OS components.
"""

import unittest
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import veil_core
import messaging_bus
import vpatch
import introspector
import foresight_engine


class TestVEILosCore(unittest.TestCase):
    """Test VEILos core kernel functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.kernel = veil_core.VEILosKernel()
        # Reset memory to default state
        self.kernel.memory = {
            "goal": "Awaiting injection",
            "quantum": {},
            "action": None
        }
        self.kernel._save_memory()
    
    def test_inject_goal(self):
        """Test goal injection"""
        result = self.kernel.inject_goal("Test goal")
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.kernel.memory["goal"], "Test goal")
    
    def test_show_memory(self):
        """Test memory display"""
        memory = self.kernel.show_memory()
        self.assertIn("goal", memory)
        self.assertIn("quantum", memory)
        self.assertIn("action", memory)
    
    def test_status(self):
        """Test status command"""
        status = self.kernel.status()
        self.assertIn("system", status)
        self.assertIn("loaded_modules", status)
        self.assertIn("memory_state", status)
    
    def test_command_execution(self):
        """Test command execution"""
        result = self.kernel.execute_command("inject_goal Test")
        self.assertEqual(result["status"], "success")


class TestMessagingBus(unittest.TestCase):
    """Test messaging bus functionality"""
    
    def setUp(self):
        """Set up test environment"""
        messaging_bus.clear_mailbox()
    
    def tearDown(self):
        """Clean up after tests"""
        messaging_bus.clear_mailbox()
    
    def test_send_signal(self):
        """Test signal sending"""
        result = messaging_bus.send_signal("test_agent", {"message": "test"})
        self.assertTrue(result)
    
    def test_receive_signal(self):
        """Test signal receiving"""
        messaging_bus.send_signal("test_agent", {"message": "test"})
        signal = messaging_bus.receive_signal("test_agent")
        self.assertIsNotNone(signal)
        self.assertEqual(signal["message"], "test")
    
    def test_list_pending_signals(self):
        """Test listing pending signals"""
        messaging_bus.send_signal("agent1", {"test": 1})
        messaging_bus.send_signal("agent2", {"test": 2})
        
        pending = messaging_bus.list_pending_signals()
        self.assertEqual(len(pending), 2)
        self.assertIn("agent1", pending)
        self.assertIn("agent2", pending)


class TestIntrospector(unittest.TestCase):
    """Test introspection functionality"""
    
    def test_capture_state(self):
        """Test state capture"""
        frame = introspector.capture_state()
        self.assertIn("timestamp", frame)
        self.assertIn("goal", frame)
        self.assertIn("quantum", frame)
        self.assertIn("action", frame)
        self.assertIn("metadata", frame)
    
    def test_analyze_history(self):
        """Test history analysis"""
        # Create some history
        introspector.capture_state()
        
        history = introspector.analyze_history(limit=5)
        self.assertIsInstance(history, list)


class TestForesightEngine(unittest.TestCase):
    """Test foresight/prediction functionality"""
    
    def test_predict_next_state(self):
        """Test state prediction"""
        prediction = foresight_engine.predict_next_state()
        self.assertIn("future_action", prediction)
        self.assertIn("risk", prediction)
        self.assertIn("confidence", prediction)
    
    def test_save_load_prediction(self):
        """Test prediction persistence"""
        prediction = foresight_engine.predict_next_state()
        pred_id = foresight_engine.save_prediction(prediction, "test_pred")
        
        loaded = foresight_engine.load_prediction("test_pred")
        self.assertEqual(loaded["future_action"], prediction["future_action"])
        
        # Clean up
        os.remove("futures/test_pred.json")


class TestModules(unittest.TestCase):
    """Test VEILos modules"""
    
    def test_quantum_observer(self):
        """Test quantum observer module"""
        sys.path.insert(0, "modules")
        import quantum_observer
        
        result = quantum_observer.run()
        self.assertEqual(result["module"], "quantum_observer")
        self.assertEqual(result["status"], "complete")
        self.assertIn("metrics", result)
    
    def test_agent_harmonizer(self):
        """Test agent harmonizer module"""
        sys.path.insert(0, "modules")
        import agent_harmonizer
        
        result = agent_harmonizer.run()
        self.assertEqual(result["module"], "agent_harmonizer")
        self.assertIn("status", result)
        self.assertIn("drift", result)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestVEILosCore))
    suite.addTests(loader.loadTestsFromTestCase(TestMessagingBus))
    suite.addTests(loader.loadTestsFromTestCase(TestIntrospector))
    suite.addTests(loader.loadTestsFromTestCase(TestForesightEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestModules))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
