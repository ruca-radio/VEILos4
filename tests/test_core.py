"""
VEIL4 Core Tests

Basic test suite for VEIL4 core functionality.
"""

import unittest
from datetime import timedelta

from core.veil4_system import VEIL4
from core.parity.unified_interface import AgentType
from core.quantum.superposition import SuperpositionManager
from core.security.capabilities import CapabilityManager


class TestQuantumSubstrate(unittest.TestCase):
    """Test quantum substrate functionality"""
    
    def setUp(self):
        self.quantum = SuperpositionManager()
    
    def test_create_superposition(self):
        """Test creating a superposition"""
        state_id = self.quantum.create_superposition(
            "test_001",
            [{"value": 1}, {"value": 2}, {"value": 3}]
        )
        self.assertEqual(state_id, "test_001")
        self.assertIn("test_001", self.quantum.superpositions)
    
    def test_observe_superposition(self):
        """Test observing a superposition causes collapse"""
        self.quantum.create_superposition(
            "test_002",
            [{"value": 1}, {"value": 2}]
        )
        
        collapsed = self.quantum.observe("test_002")
        self.assertIn(collapsed.state_data["value"], [1, 2])
        self.assertNotIn("test_002", self.quantum.superpositions)
        self.assertIn("test_002", self.quantum.collapsed_states)


class TestCapabilitySecurity(unittest.TestCase):
    """Test capability security system"""
    
    def setUp(self):
        self.security = CapabilityManager()
    
    def test_issue_capability(self):
        """Test issuing a capability"""
        cap = self.security.issue_capability(
            resource="test_resource",
            permissions={"read", "write"},
            issued_to="user_001"
        )
        self.assertIsNotNone(cap.token)
        self.assertTrue(cap.is_valid())
    
    def test_verify_capability(self):
        """Test verifying a capability"""
        cap = self.security.issue_capability(
            resource="test_resource",
            permissions={"read"},
            issued_to="user_001"
        )
        
        # Should have read permission
        self.assertTrue(
            self.security.verify_capability(cap.token, "test_resource", "read")
        )
        
        # Should not have write permission
        self.assertFalse(
            self.security.verify_capability(cap.token, "test_resource", "write")
        )
    
    def test_revoke_capability(self):
        """Test revoking a capability"""
        cap = self.security.issue_capability(
            resource="test_resource",
            permissions={"read"},
            issued_to="user_001"
        )
        
        # Valid before revocation
        self.assertTrue(cap.is_valid())
        
        # Revoke
        self.security.revoke_capability(cap.token)
        
        # Invalid after revocation
        self.assertFalse(cap.is_valid())


class TestVEIL4System(unittest.TestCase):
    """Test integrated VEIL4 system"""
    
    def setUp(self):
        self.veil4 = VEIL4()
        self.veil4.start()
    
    def tearDown(self):
        self.veil4.shutdown()
    
    def test_register_agent(self):
        """Test registering an agent"""
        agent = self.veil4.register_agent(
            agent_id="test_user",
            agent_type=AgentType.HUMAN,
            capabilities=["read"]
        )
        self.assertEqual(agent.agent_id, "test_user")
        self.assertIn("test_user", self.veil4.parity.agents)
    
    def test_quantum_workflow(self):
        """Test quantum superposition and observation workflow"""
        # Create superposition
        state_id = self.veil4.create_quantum_state(
            "test_state",
            [{"choice": "A"}, {"choice": "B"}]
        )
        
        # Register observer
        self.veil4.register_agent(
            "observer",
            AgentType.HUMAN,
            []
        )
        
        # Observe
        result = self.veil4.observe_quantum_state(state_id, "observer")
        self.assertIn(result["choice"], ["A", "B"])
    
    def test_capability_workflow(self):
        """Test capability grant and verification workflow"""
        # Register agent
        self.veil4.register_agent(
            "user_001",
            AgentType.HUMAN,
            []
        )
        
        # Grant capability
        token = self.veil4.grant_capability(
            resource="data",
            permissions=["read"],
            agent_id="user_001",
            duration_seconds=3600
        )
        
        # Verify access
        has_access = self.veil4.verify_access(
            agent_id="user_001",
            resource="data",
            permission="read",
            capability_token=token
        )
        self.assertTrue(has_access)
    
    def test_audit_log(self):
        """Test audit logging"""
        initial_count = len(self.veil4.audit.transitions)
        
        # Perform an operation
        self.veil4.register_agent(
            "test_agent",
            AgentType.MODEL,
            []
        )
        
        # Check audit log increased
        new_count = len(self.veil4.audit.transitions)
        self.assertGreater(new_count, initial_count)
        
        # Verify log integrity
        self.assertTrue(self.veil4.audit.verify_chain())


if __name__ == "__main__":
    unittest.main()
