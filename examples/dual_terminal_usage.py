"""
Example: Dual VEILos4 and Linux Terminal Usage

Demonstrates how to use the terminal as both a VEILos4 command interface
and a Linux shell emulator. This is particularly useful for AI models that
need to interact with both VEILos4 system and execute Linux commands.
"""

from surface.terminal.terminal_backend import TerminalBackend
from core.veil4_system import VEIL4


def demo_dual_terminal():
    """Demonstrate dual terminal functionality"""
    
    print("=" * 60)
    print("VEILos4 Dual Terminal Demo")
    print("=" * 60)
    print()
    
    # Initialize VEIL4 and terminal backend
    veil4 = VEIL4()
    terminal = TerminalBackend(veil4)
    terminal.start()
    
    print("✓ VEIL4 system started")
    print("✓ Terminal backend initialized")
    print()
    
    # Create a terminal session
    boot_settings = {
        "userMode": "user",
        "networkEnabled": True,
        "pluginManagerEnabled": True
    }
    
    session = terminal.create_session("demo_session", boot_settings)
    session_id = session["session_id"]
    
    print(f"✓ Session created: {session_id}")
    print(f"  Agent ID: {session['agent_id']}")
    print(f"  Working Directory: {session['cwd']}")
    print()
    
    # Demo 1: VEILos4 Commands
    print("=" * 60)
    print("DEMO 1: VEILos4 Commands")
    print("=" * 60)
    print()
    
    commands = [
        ("help", "Get help information"),
        ("quantum create demo_state", "Create quantum superposition"),
        ("quantum list", "List quantum states"),
        ("agent register ai_model MODEL", "Register an AI agent"),
        ("agent list", "List all agents"),
        ("status", "Get system status")
    ]
    
    for cmd, description in commands:
        print(f"Command: {cmd}")
        print(f"Purpose: {description}")
        result = terminal.execute_command(session_id, cmd)
        
        if result["success"]:
            output = result["output"]
            # Truncate long output
            if len(output) > 200:
                output = output[:200] + "..."
            print(f"Output:\n{output}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("-" * 60)
        print()
    
    # Demo 2: Linux Shell Commands
    print("=" * 60)
    print("DEMO 2: Linux Shell Commands")
    print("=" * 60)
    print()
    
    shell_commands = [
        ("pwd", "Print working directory"),
        ("ls /tmp", "List /tmp directory"),
        ("echo 'Hello from VEILos4 terminal'", "Echo a message"),
        ("cd /tmp", "Change to /tmp directory"),
        ("pwd", "Verify directory changed"),
        ("export TEST_VAR=test_value", "Set environment variable"),
        ("shell info", "Show shell information")
    ]
    
    for cmd, description in shell_commands:
        print(f"Command: {cmd}")
        print(f"Purpose: {description}")
        result = terminal.execute_command(session_id, cmd)
        
        if result["success"]:
            output = result["output"]
            print(f"Output: {output}")
            if "cwd" in result and result["cwd"]:
                print(f"Working Directory: {result['cwd']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("-" * 60)
        print()
    
    # Demo 3: Mixed Commands (VEILos4 and Linux interleaved)
    print("=" * 60)
    print("DEMO 3: Mixed Commands")
    print("=" * 60)
    print()
    
    mixed_commands = [
        "quantum create mixed_state",
        "ls",
        "agent register shell_user HUMAN",
        "echo 'Executing from VEILos4 terminal'",
        "quantum observe mixed_state",
        "pwd"
    ]
    
    for cmd in mixed_commands:
        print(f"$ {cmd}")
        result = terminal.execute_command(session_id, cmd)
        
        if result["success"]:
            output = result["output"]
            if len(output) > 150:
                output = output[:150] + "..."
            print(output)
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print()
    
    # Demo 4: Explicit Linux Prefix
    print("=" * 60)
    print("DEMO 4: Explicit Linux Command Prefix")
    print("=" * 60)
    print()
    
    print("Using 'linux' prefix for explicit shell execution:")
    print()
    
    result = terminal.execute_command(session_id, "linux echo 'This is explicitly a Linux command'")
    print(f"Command: linux echo 'This is explicitly a Linux command'")
    print(f"Output: {result['output']}")
    print()
    
    # Demo 5: AI Model Usage Pattern
    print("=" * 60)
    print("DEMO 5: AI Model Usage Pattern")
    print("=" * 60)
    print()
    
    print("Simulating AI model interaction:")
    print()
    
    # Register AI model as agent
    result = terminal.execute_command(session_id, "agent register gpt4_agent MODEL")
    print(f"1. Register as agent: {result['output'][:80]}...")
    print()
    
    # AI can create quantum states for decision making
    result = terminal.execute_command(session_id, "quantum create ai_decision")
    print(f"2. Create quantum state: {result['output'][:80]}...")
    print()
    
    # AI can execute Linux commands to gather information
    result = terminal.execute_command(session_id, "ls /etc")
    print(f"3. Gather system info: Found {len(result['output'].split())} items in /etc")
    print()
    
    # AI can check system status
    result = terminal.execute_command(session_id, "status")
    print(f"4. Check system status: {result['output'][:80]}...")
    print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("The VEILos4 terminal now supports:")
    print("  ✓ VEILos4 commands (quantum, agent, capability, plugin)")
    print("  ✓ Linux shell commands (ls, cd, pwd, echo, etc.)")
    print("  ✓ Auto-detection of command type")
    print("  ✓ Session-based shell state (cwd, env)")
    print("  ✓ Security controls (capability-based)")
    print("  ✓ AI model accessibility via API")
    print()
    print("AI models can:")
    print("  - Execute both VEILos4 and Linux commands")
    print("  - Maintain shell state across commands")
    print("  - Access system information")
    print("  - Interact with quantum substrate")
    print("  - Manage agents and capabilities")
    print()
    
    # Cleanup
    terminal.close_session(session_id)
    veil4.shutdown()
    
    print("✓ Demo complete!")


if __name__ == "__main__":
    demo_dual_terminal()
