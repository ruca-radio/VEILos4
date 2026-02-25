"""
Loop Manager Module
===================
Cognitive loop agent that watches memory for GOAL and triggers recursive actions.
"""

import json
import time


MEMORY_PATH = "memory_store.json"
MAX_DEPTH = 6


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
    Main loop manager execution.
    Recursively checks and corrects based on drift.
    """
    mem = load_memory()
    depth = mem.get("loop_depth", 0)
    
    print(f"[LoopManager] Current depth: {depth}")
    
    # Check recursion limit
    if depth >= MAX_DEPTH:
        print(f"[!] Recursion limit hit. Depth={depth}")
        mem["action"] = "MAX_DEPTH_REACHED"
        save_memory(mem)
        return {
            "status": "limit_reached",
            "depth": depth,
            "max_depth": MAX_DEPTH
        }
    
    # Check drift
    drift = mem.get("quantum", {}).get("drift", 0)
    
    if drift > 0.05:
        # Trigger recursive correction
        mem["action"] = "RECURSIVE_CORRECTION"
        mem["loop_depth"] = depth + 1
        save_memory(mem)
        
        print(f"[↻] Drift={drift}. Recursive correction initiated. Depth={depth+1}")
        
        return {
            "status": "correction_initiated",
            "drift": drift,
            "depth": depth + 1,
            "action": "RECURSIVE_CORRECTION"
        }
    else:
        # Drift is acceptable, halt loop
        print("[✓] Drift normal. Loop halted.")
        mem["action"] = "STABLE"
        mem["loop_depth"] = 0  # Reset depth
        save_memory(mem)
        
        return {
            "status": "stable",
            "drift": drift,
            "depth": 0,
            "action": "STABLE"
        }


if __name__ == "__main__":
    run()
