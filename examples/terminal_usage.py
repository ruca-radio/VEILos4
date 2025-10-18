"""
VEILos4 Terminal Usage Example

Demonstrates how to use the terminal backend programmatically.
"""

from surface.terminal.terminal_backend import TerminalBackend
from core.veil4_system import VEIL4


def main():
    print("=" * 60)
    print("VEILos4 Terminal Backend Example")
    print("=" * 60)
    
    # Initialize VEIL4 and Terminal
    print("\n1. Initializing VEIL4 system...")
    veil4 = VEIL4()
    terminal = TerminalBackend(veil4)
    terminal.start()
    print(f"   ✓ VEIL4 running: {veil4.running}")
    
    # Create a terminal session
    print("\n2. Creating terminal session...")
    boot_settings = {
        "userMode": "sudo",
        "networkEnabled": True,
        "pluginManagerEnabled": True,
        "multimodelEnabled": False,
        "agenticEnabled": True
    }
    session_info = terminal.create_session("example_session_001", boot_settings)
    print(f"   ✓ Session ID: {session_info['session_id']}")
    print(f"   ✓ Agent ID: {session_info['agent_id']}")
    
    # Execute some commands
    print("\n3. Executing commands...")
    
    commands = [
        "help",
        "status",
        "quantum create example_state",
        "quantum list",
        "agent register alice HUMAN",
        "agent register gpt4 MODEL",
        "agent list",
        "quantum observe example_state",
    ]
    
    for cmd in commands:
        print(f"\n   $ {cmd}")
        result = terminal.execute_command("example_session_001", cmd)
        
        if result["success"]:
            output = result["output"]
            # Truncate long output for display
            if len(output) > 200:
                output = output[:200] + "..."
            print(f"   {output}")
        else:
            print(f"   ✗ Error: {result.get('error', 'Unknown error')}")
    
    # Show system status
    print("\n4. System Status:")
    status = terminal.get_status()
    print(f"   Running: {status['running']}")
    print(f"   Active Sessions: {status['active_sessions']}")
    print(f"   Total Commands: {status['command_history_size']}")
    
    # Get VEIL4 system status
    veil4_status = veil4.get_system_status()
    print(f"\n5. VEIL4 Core Status:")
    print(f"   Agents: {veil4_status['num_agents']}")
    print(f"   Plugins: {veil4_status['num_plugins']}")
    print(f"   Superpositions: {veil4_status['num_superpositions']}")
    print(f"   Transitions: {veil4_status['num_transitions']}")
    
    # Cleanup
    print("\n6. Closing session...")
    terminal.close_session("example_session_001")
    veil4.shutdown()
    print("   ✓ Session closed")
    print("   ✓ VEIL4 shutdown")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
