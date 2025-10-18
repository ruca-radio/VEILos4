"""
VEIL4 Example: Basic System Usage

Demonstrates the core functionality of VEIL4 including:
- Agent registration (human and AI models)
- Quantum state superposition and observation
- Capability-based security
- Audit logging
"""

from core.veil4_system import VEIL4
from core.parity.unified_interface import AgentType


def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  VEIL4 Example: Basic System Usage                           ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    # Initialize VEIL4
    print("1. Initializing VEIL4 system...")
    veil4 = VEIL4(config={
        "coherence_time": 60.0  # States remain coherent for 60 seconds
    })
    veil4.start()
    print("   ✓ VEIL4 system started\n")
    
    # Register agents
    print("2. Registering agents...")
    
    # Register human user
    human_agent = veil4.register_agent(
        agent_id="alice",
        agent_type=AgentType.HUMAN,
        capabilities=["read", "write", "observe"],
        metadata={"name": "Alice", "role": "researcher"}
    )
    print(f"   ✓ Human agent registered: {human_agent.agent_id}")
    
    # Register AI model
    model_agent = veil4.register_agent(
        agent_id="gpt4",
        agent_type=AgentType.MODEL,
        capabilities=["reason", "generate", "observe"],
        metadata={"model": "gpt-4", "version": "2025.1"}
    )
    print(f"   ✓ Model agent registered: {model_agent.agent_id}\n")
    
    # Create quantum superposition
    print("3. Creating quantum superposition...")
    state_id = veil4.create_quantum_state(
        state_id="experiment_001",
        states=[
            {"outcome": "success", "confidence": 0.8, "data": "positive"},
            {"outcome": "partial", "confidence": 0.5, "data": "neutral"},
            {"outcome": "failure", "confidence": 0.2, "data": "negative"}
        ],
        amplitudes=[0.632, 0.447, 0.632]  # Custom probability amplitudes
    )
    print(f"   ✓ Superposition created: {state_id}")
    
    # Check superposition info
    info = veil4.quantum.get_superposition_info(state_id)
    print(f"   ✓ States in superposition: {info['num_states']}")
    for i, state in enumerate(info['states']):
        print(f"     - State {i+1}: {state['data']['outcome']} "
              f"(probability: {state['probability']:.3f})")
    print()
    
    # Observe quantum state (causes collapse)
    print("4. Observing quantum state (causing collapse)...")
    collapsed_state = veil4.observe_quantum_state(state_id, "alice")
    print(f"   ✓ State collapsed to: {collapsed_state['outcome']}")
    print(f"     Data: {collapsed_state['data']}\n")
    
    # Grant capabilities
    print("5. Granting capabilities...")
    token = veil4.grant_capability(
        resource="experimental_data",
        permissions=["read", "write"],
        agent_id="alice",
        duration_seconds=3600  # Valid for 1 hour
    )
    print(f"   ✓ Capability granted to alice")
    print(f"     Token: {token[:16]}...")
    print(f"     Resource: experimental_data")
    print(f"     Permissions: read, write")
    print(f"     Duration: 3600 seconds\n")
    
    # Verify access
    print("6. Verifying access...")
    has_read_access = veil4.verify_access(
        agent_id="alice",
        resource="experimental_data",
        permission="read",
        capability_token=token
    )
    print(f"   ✓ Alice read access: {has_read_access}")
    
    has_delete_access = veil4.verify_access(
        agent_id="alice",
        resource="experimental_data",
        permission="delete",
        capability_token=token
    )
    print(f"   ✓ Alice delete access: {has_delete_access}\n")
    
    # Get system status
    print("7. System status...")
    status = veil4.get_system_status()
    print(f"   Running: {status['running']}")
    print(f"   Agents: {status['num_agents']}")
    print(f"   Plugins: {status['num_plugins']}")
    print(f"   Superpositions: {status['num_superpositions']}")
    print(f"   Audit transitions: {status['num_transitions']}\n")
    
    # View audit log
    print("8. Recent audit log entries...")
    recent = veil4.audit.get_recent_transitions(5)
    for transition in recent:
        print(f"   - {transition.operation} by {transition.agent_id}")
        print(f"     Time: {transition.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     Hash: {transition.transition_hash[:16]}...")
    print()
    
    # Verify audit log integrity
    print("9. Verifying audit log integrity...")
    is_valid = veil4.audit.verify_chain()
    print(f"   ✓ Audit log valid: {is_valid}\n")
    
    # Shutdown
    print("10. Shutting down VEIL4...")
    veil4.shutdown()
    print("    ✓ VEIL4 system stopped\n")
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  Example completed successfully!                              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
