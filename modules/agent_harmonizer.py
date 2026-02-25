"""
Agent Harmonizer Module
========================
Monitors quantum drift and engages harmonization when threshold exceeded.
"""

import json


MEMORY_PATH = "memory_store.json"
DRIFT_THRESHOLD = 0.05


def load_memory():
    """Load memory from JSON store"""
    try:
        with open(MEMORY_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"goal": "Awaiting injection", "quantum": {}, "action": None}


def save_memory(mem):
    """Save memory to JSON store"""
    with open(MEMORY_PATH, 'w') as f:
        json.dump(mem, f, indent=2)


def run():
    """
    Main module execution.
    Reads drift and activates harmonizer if needed.
    """
    # Load current memory
    mem = load_memory()
    
    # Get drift value
    drift = mem.get("quantum", {}).get("drift", 0)
    
    # Check if harmonization needed
    if drift > DRIFT_THRESHOLD:
        mem["action"] = "harmonizer_engaged"
        status_msg = f"Drift {drift:.4f} > threshold {DRIFT_THRESHOLD}. Harmonizer engaged."
        result_status = "engaged"
    else:
        mem["action"] = "stable"
        status_msg = f"Drift {drift:.4f} within acceptable range. System stable."
        result_status = "stable"
    
    # Save updated memory
    save_memory(mem)
    
    result = {
        "module": "agent_harmonizer",
        "status": result_status,
        "drift": drift,
        "threshold": DRIFT_THRESHOLD,
        "message": status_msg
    }
    
    print(f"[AgentHarmonizer] {status_msg}")
    
    return result


if __name__ == "__main__":
    run()
