"""
Tests for VEILos4 Terminal Backend

Tests the terminal backend integration with VEIL4 core.
"""

import unittest
from surface.terminal.terminal_backend import TerminalBackend
from core.veil4_system import VEIL4


class TestTerminalBackend(unittest.TestCase):
    """Test Terminal Backend functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.veil4 = VEIL4()
        self.terminal = TerminalBackend(self.veil4)
        self.terminal.start()
    
    def tearDown(self):
        """Cleanup"""
        if self.veil4.running:
            self.veil4.shutdown()
    
    def test_terminal_start(self):
        """Test terminal backend starts successfully"""
        self.assertTrue(self.veil4.running)
        self.assertEqual(len(self.terminal.terminal_sessions), 0)
    
    def test_create_session(self):
        """Test creating a terminal session"""
        boot_settings = {
            "userMode": "user",
            "networkEnabled": True,
            "pluginManagerEnabled": True
        }
        
        session_info = self.terminal.create_session("test_session_001", boot_settings)
        
        self.assertEqual(session_info["session_id"], "test_session_001")
        self.assertEqual(session_info["status"], "active")
        self.assertTrue(session_info["veil4_running"])
        self.assertIsNotNone(session_info["agent_id"])
        
        # Verify session was stored
        self.assertIn("test_session_001", self.terminal.terminal_sessions)
    
    def test_execute_quantum_create(self):
        """Test quantum create command"""
        # Create session
        self.terminal.create_session("test_session_002", {"userMode": "user"})
        
        # Execute quantum create command
        result = self.terminal.execute_command(
            "test_session_002",
            "quantum create test_state"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("created", result["output"])
        
        # Verify quantum state was created in VEIL4
        self.assertIn("test_state", self.veil4.quantum.superpositions)
    
    def test_execute_quantum_observe(self):
        """Test quantum observe command"""
        # Create session
        self.terminal.create_session("test_session_003", {"userMode": "user"})
        
        # Create a quantum state first
        self.terminal.execute_command("test_session_003", "quantum create test_state_2")
        
        # Observe the state
        result = self.terminal.execute_command(
            "test_session_003",
            "quantum observe test_state_2"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("collapsed", result["output"])
    
    def test_execute_quantum_list(self):
        """Test quantum list command"""
        # Create session
        self.terminal.create_session("test_session_004", {"userMode": "user"})
        
        # Create some quantum states
        self.terminal.execute_command("test_session_004", "quantum create state_1")
        self.terminal.execute_command("test_session_004", "quantum create state_2")
        
        # List states
        result = self.terminal.execute_command("test_session_004", "quantum list")
        
        self.assertTrue(result["success"])
        self.assertIn("state_1", result["output"])
        self.assertIn("state_2", result["output"])
    
    def test_execute_agent_register(self):
        """Test agent register command"""
        # Create session
        self.terminal.create_session("test_session_005", {"userMode": "user"})
        
        # Register an agent
        result = self.terminal.execute_command(
            "test_session_005",
            "agent register test_agent HUMAN"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("registered", result["output"])
        
        # Verify agent was registered in VEIL4
        self.assertIn("test_agent", self.veil4.parity.agents)
    
    def test_execute_agent_list(self):
        """Test agent list command"""
        # Create session
        self.terminal.create_session("test_session_006", {"userMode": "user"})
        
        # Register some agents
        self.terminal.execute_command("test_session_006", "agent register agent1 HUMAN")
        self.terminal.execute_command("test_session_006", "agent register agent2 MODEL")
        
        # List agents
        result = self.terminal.execute_command("test_session_006", "agent list")
        
        self.assertTrue(result["success"])
        self.assertIn("agent1", result["output"])
        self.assertIn("agent2", result["output"])
    
    def test_execute_status_command(self):
        """Test status command"""
        # Create session
        self.terminal.create_session("test_session_007", {"userMode": "user"})
        
        # Get status
        result = self.terminal.execute_command("test_session_007", "status")
        
        self.assertTrue(result["success"])
        self.assertIn("System Status", result["output"])
        self.assertIn("Running", result["output"])
    
    def test_execute_help_command(self):
        """Test help command"""
        # Create session
        self.terminal.create_session("test_session_008", {"userMode": "user"})
        
        # Get help
        result = self.terminal.execute_command("test_session_008", "help")
        
        self.assertTrue(result["success"])
        self.assertIn("Commands", result["output"])
        self.assertIn("quantum", result["output"])
        self.assertIn("agent", result["output"])
    
    def test_execute_unknown_command(self):
        """Test handling of unknown command"""
        # Create session
        self.terminal.create_session("test_session_009", {"userMode": "user"})
        
        # Execute unknown command
        result = self.terminal.execute_command(
            "test_session_009",
            "nonexistent_command arg1 arg2"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Unknown", result["output"])
    
    def test_command_history(self):
        """Test command history tracking"""
        # Create session
        self.terminal.create_session("test_session_010", {"userMode": "user"})
        
        # Execute multiple commands
        self.terminal.execute_command("test_session_010", "help")
        self.terminal.execute_command("test_session_010", "status")
        self.terminal.execute_command("test_session_010", "quantum list")
        
        # Verify commands were logged
        self.assertGreaterEqual(len(self.terminal.command_history), 3)
        
        # Check command history contains our commands
        commands = [entry["command"] for entry in self.terminal.command_history]
        self.assertIn("help", commands)
        self.assertIn("status", commands)
        self.assertIn("quantum list", commands)
    
    def test_session_info(self):
        """Test getting session info"""
        # Create session
        boot_settings = {"userMode": "sudo"}
        self.terminal.create_session("test_session_011", boot_settings)
        
        # Get session info
        info = self.terminal.get_session_info("test_session_011")
        
        self.assertIsNotNone(info)
        self.assertEqual(info["id"], "test_session_011")
        self.assertEqual(info["state"], "active")
        self.assertEqual(info["boot_settings"]["userMode"], "sudo")
    
    def test_close_session(self):
        """Test closing a session"""
        # Create session
        self.terminal.create_session("test_session_012", {"userMode": "user"})
        
        # Close session
        success = self.terminal.close_session("test_session_012")
        
        self.assertTrue(success)
        
        # Verify session state changed
        info = self.terminal.get_session_info("test_session_012")
        self.assertEqual(info["state"], "closed")
    
    def test_get_status(self):
        """Test getting backend status"""
        status = self.terminal.get_status()
        
        self.assertTrue(status["running"])
        self.assertIn("veil4_status", status)
        self.assertIn("active_sessions", status)
        self.assertIn("total_sessions", status)
    
    def test_sudo_mode_capabilities(self):
        """Test sudo mode grants admin capabilities"""
        # Create session with sudo mode
        boot_settings = {"userMode": "sudo"}
        session_info = self.terminal.create_session("test_session_013", boot_settings)
        
        agent_id = session_info["agent_id"]
        agent = self.veil4.parity.agents[agent_id]
        
        # Verify admin capabilities were granted
        self.assertIn("admin", agent.capabilities)
    
    def test_user_mode_capabilities(self):
        """Test user mode has limited capabilities"""
        # Create session with user mode
        boot_settings = {"userMode": "user"}
        session_info = self.terminal.create_session("test_session_014", boot_settings)
        
        agent_id = session_info["agent_id"]
        agent = self.veil4.parity.agents[agent_id]
        
        # Verify limited capabilities
        self.assertNotIn("admin", agent.capabilities)
        self.assertIn("read", agent.capabilities)
        self.assertIn("execute", agent.capabilities)


if __name__ == "__main__":
    unittest.main()
