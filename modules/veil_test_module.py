"""
VEIL Test Module
================
Simple test module to verify module loading system.
"""

import json


MEMORY_PATH = "memory_store.json"


def load_memory():
    """Load memory from JSON store"""
    try:
        with open(MEMORY_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"goal": "Awaiting injection", "quantum": {}, "action": None}


def run():
    """
    Main module execution.
    Simple test that reads memory and returns status.
    """
    mem = load_memory()
    
    result = {
        "module": "veil_test_module",
        "status": "success",
        "message": "Test module executed successfully",
        "current_goal": mem.get("goal", "None"),
        "current_action": mem.get("action", "None")
    }
    
    print("[VEILTestModule] Test execution complete")
    
    return result


if __name__ == "__main__":
    run()
