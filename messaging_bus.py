"""
Messaging Bus
=============
Simulated pub/sub event system for agent communication.
Agents can send and receive signals via mailbox files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


MAILBOX_PATH = "mailbox/"


def send_signal(target_agent: str, message: Dict[str, Any]) -> bool:
    """
    Send a signal to a target agent.
    
    Args:
        target_agent: Agent ID to send signal to
        message: Message payload
        
    Returns:
        True if signal sent successfully
    """
    # Ensure mailbox directory exists
    Path(MAILBOX_PATH).mkdir(exist_ok=True)
    
    # Create signal file
    signal_path = os.path.join(MAILBOX_PATH, f"{target_agent}.signal.json")
    
    try:
        with open(signal_path, 'w') as f:
            json.dump(message, f, indent=2)
        
        print(f"[✉] Signal sent to {target_agent}")
        return True
    
    except Exception as e:
        print(f"[✗] Failed to send signal to {target_agent}: {e}")
        return False


def receive_signal(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Receive a signal for an agent.
    
    Args:
        agent_id: Agent ID to check for signals
        
    Returns:
        Message payload if signal exists, None otherwise
    """
    signal_path = os.path.join(MAILBOX_PATH, f"{agent_id}.signal.json")
    
    if not os.path.exists(signal_path):
        return None
    
    try:
        with open(signal_path, 'r') as f:
            msg = json.load(f)
        
        # Delete signal after reading (consume it)
        os.remove(signal_path)
        
        print(f"[✉] Signal received by {agent_id}")
        return msg
    
    except Exception as e:
        print(f"[✗] Failed to receive signal for {agent_id}: {e}")
        return None


def list_pending_signals() -> list:
    """
    List all pending signals in mailbox.
    
    Returns:
        List of agent IDs with pending signals
    """
    if not os.path.exists(MAILBOX_PATH):
        return []
    
    signals = []
    for filename in os.listdir(MAILBOX_PATH):
        if filename.endswith(".signal.json"):
            agent_id = filename.replace(".signal.json", "")
            signals.append(agent_id)
    
    return signals


def clear_mailbox():
    """Clear all pending signals"""
    if not os.path.exists(MAILBOX_PATH):
        return
    
    for filename in os.listdir(MAILBOX_PATH):
        if filename.endswith(".signal.json"):
            os.remove(os.path.join(MAILBOX_PATH, filename))
    
    print("[✓] Mailbox cleared")


# Example usage
if __name__ == "__main__":
    # Send test signal
    send_signal("harmonizer_agent", {
        "from": "quantum_supervisor",
        "event": "drift_event",
        "payload": {
            "drift": 0.056
        }
    })
    
    # Check pending signals
    pending = list_pending_signals()
    print(f"Pending signals: {pending}")
    
    # Receive signal
    msg = receive_signal("harmonizer_agent")
    if msg:
        print(f"Received: {json.dumps(msg, indent=2)}")
