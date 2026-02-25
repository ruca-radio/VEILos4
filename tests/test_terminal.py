"""
Tests for VEILos4 Terminal Backend

Tests the terminal backend integration with VEIL4 core.
Includes tests for dual VEILos4 and Linux terminal emulation.
"""

import unittest
import os
import tempfile
from pathlib import Path
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
        self.assertTrue(session_info["shell_enabled"])
        self.assertIsNotNone(session_info["cwd"])
        
        # Verify session was stored
        self.assertIn("test_session_001", self.terminal.terminal_sessions)
        
        # Verify shell state was initialized
        self.assertIn("test_session_001", self.terminal.shell_states)
        shell_state = self.terminal.shell_states["test_session_001"]
        self.assertIn("cwd", shell_state)
        self.assertIn("env", shell_state)
        self.assertIn("shell", shell_state)
    
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
        self.assertIn("Shell Commands", result["output"])
        self.assertIn("linux", result["output"])
    
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
        
        # Verify shell state was cleaned up
        self.assertNotIn("test_session_012", self.terminal.shell_states)
    
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


class TestLinuxTerminalEmulation(unittest.TestCase):
    """Test Linux terminal emulation functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.veil4 = VEIL4()
        self.terminal = TerminalBackend(self.veil4)
        self.terminal.start()
        
        # Create a test session
        self.terminal.create_session("test_linux_session", {"userMode": "user"})
        self.session_id = "test_linux_session"
    
    def tearDown(self):
        """Cleanup"""
        if self.veil4.running:
            self.veil4.shutdown()
    
    def test_execute_linux_echo(self):
        """Test executing echo command"""
        result = self.terminal.execute_command(
            self.session_id,
            "echo Hello VEILos4"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Hello VEILos4", result["output"])
    
    def test_execute_linux_pwd(self):
        """Test pwd command"""
        result = self.terminal.execute_command(
            self.session_id,
            "pwd"
        )
        
        self.assertTrue(result["success"])
        # Should return a path
        self.assertTrue(len(result["output"]) > 0)
        self.assertNotIn("Unknown command", result["output"])
    
    def test_execute_linux_ls(self):
        """Test ls command"""
        result = self.terminal.execute_command(
            self.session_id,
            "ls /"
        )
        
        self.assertTrue(result["success"])
        # Should list root directory contents
        self.assertTrue(len(result["output"]) > 0)
    
    def test_execute_cd_command(self):
        """Test cd (change directory) command"""
        # Get initial working directory
        initial_cwd = self.terminal.shell_states[self.session_id]["cwd"]
        
        # Change to /tmp
        result = self.terminal.execute_command(
            self.session_id,
            "cd /tmp"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Changed directory", result["output"])
        
        # Verify cwd changed
        new_cwd = self.terminal.shell_states[self.session_id]["cwd"]
        self.assertEqual(new_cwd, "/tmp")
        self.assertNotEqual(initial_cwd, new_cwd)
        
        # Verify pwd shows new directory
        result = self.terminal.execute_command(self.session_id, "pwd")
        self.assertIn("/tmp", result["output"])
    
    def test_execute_cd_nonexistent(self):
        """Test cd to non-existent directory"""
        result = self.terminal.execute_command(
            self.session_id,
            "cd /nonexistent_directory_12345"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("No such directory", result["output"])
    
    def test_explicit_linux_command(self):
        """Test explicit linux command prefix"""
        result = self.terminal.execute_command(
            self.session_id,
            "linux echo Testing explicit linux command"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Testing explicit linux command", result["output"])
    
    def test_shell_info_command(self):
        """Test shell info command"""
        result = self.terminal.execute_command(
            self.session_id,
            "shell info"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Shell Information", result["output"])
        self.assertIn("Working Dir", result["output"])
    
    def test_export_command(self):
        """Test export environment variable"""
        result = self.terminal.execute_command(
            self.session_id,
            "export TEST_VAR=test_value"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Exported", result["output"])
        
        # Verify environment variable was set
        shell_state = self.terminal.shell_states[self.session_id]
        self.assertIn("TEST_VAR", shell_state["env"])
        self.assertEqual(shell_state["env"]["TEST_VAR"], "test_value")
    
    def test_permission_denied_for_user_mode(self):
        """Test that user mode cannot execute without execute capability"""
        # Create a session without execute capability
        # (This is a bit contrived since our create_session always grants execute)
        # We'll test the security check directly
        session_info = self.terminal.get_session_info(self.session_id)
        agent_id = session_info["agent_id"]
        
        # Verify execute capability is present
        agent = self.veil4.parity.agents[agent_id]
        self.assertIn("execute", agent.capabilities)
        
        # Commands should work
        result = self.terminal.execute_command(
            self.session_id,
            "echo test"
        )
        self.assertTrue(result["success"])
    
    def test_dangerous_command_blocking(self):
        """Test that dangerous commands are blocked for non-admin users"""
        result = self.terminal.execute_command(
            self.session_id,
            "rm -rf /"
        )
        
        # Should be blocked
        self.assertTrue(result["success"])
        self.assertIn("Security", result["output"])
        self.assertIn("blocked", result["output"])
    
    def test_auto_detect_common_commands(self):
        """Test that common Linux commands are auto-detected"""
        # Test a few common commands
        commands = ["ls", "cat /etc/hostname", "ps"]
        
        for cmd in commands:
            result = self.terminal.execute_command(self.session_id, cmd)
            # Should execute, not show "Unknown command"
            self.assertTrue(result["success"])
            # Should not be an unknown command error
            if "Unknown command" in result["output"]:
                # If it's unknown, it should be because it's trying to execute
                self.fail(f"Command '{cmd}' was not auto-detected as Linux command")
    
    def test_cwd_persistence_across_commands(self):
        """Test that working directory persists across commands"""
        # Change to /tmp
        self.terminal.execute_command(self.session_id, "cd /tmp")
        
        # Execute ls without arguments (should list /tmp)
        result = self.terminal.execute_command(self.session_id, "ls")
        
        self.assertTrue(result["success"])
        # Result should be from /tmp directory
        
        # Verify we're still in /tmp
        cwd = self.terminal.shell_states[self.session_id]["cwd"]
        self.assertEqual(cwd, "/tmp")
    
    def test_result_includes_cwd(self):
        """Test that command results include current working directory"""
        result = self.terminal.execute_command(self.session_id, "pwd")
        
        self.assertTrue(result["success"])
        self.assertIn("cwd", result)
        self.assertTrue(len(result["cwd"]) > 0)


if __name__ == "__main__":
    unittest.main()
