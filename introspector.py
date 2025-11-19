"""
Introspector
============
Crawls memory, call logs, and directive chains for reasoning traces.
Captures system snapshots for analysis.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


STACKFRAMES_PATH = "stackframes/"


def capture_state(memory_file: str = "memory_store.json", 
                  log_file: str = "logs/kernel_boot.log") -> Dict[str, Any]:
    """
    Capture current system state as introspective frame.
    
    Args:
        memory_file: Path to memory store
        log_file: Path to kernel log
        
    Returns:
        State snapshot
    """
    # Ensure stackframes directory exists
    Path(STACKFRAMES_PATH).mkdir(exist_ok=True)
    
    # Load current memory state
    try:
        with open(memory_file, 'r') as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}
    
    # Create introspection frame
    frame = {
        "timestamp": datetime.now().isoformat(),
        "goal": state.get("goal", None),
        "quantum": state.get("quantum", {}),
        "action": state.get("action", None),
        "stack_hint": state.get("loop_depth", 0)
    }
    
    # Add metadata
    frame["metadata"] = {
        "captured_by": "introspector",
        "system_time": time.time()
    }
    
    # Save frame
    frame_name = f"trace_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"
    frame_path = Path(STACKFRAMES_PATH) / frame_name
    
    with open(frame_path, 'w') as f:
        json.dump(frame, f, indent=2)
    
    print(f"[🧠] Introspective frame saved: {frame_path}")
    
    return frame


def analyze_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Analyze recent stackframes to identify patterns.
    
    Args:
        limit: Maximum number of frames to analyze
        
    Returns:
        Analysis results
    """
    stackframes_dir = Path(STACKFRAMES_PATH)
    
    if not stackframes_dir.exists():
        return []
    
    # Get all stackframes, sorted by modification time
    frames = sorted(
        stackframes_dir.glob("trace_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:limit]
    
    analysis = []
    
    for frame_path in frames:
        with open(frame_path, 'r') as f:
            frame = json.load(f)
        
        analysis.append({
            "timestamp": frame.get("timestamp"),
            "goal": frame.get("goal"),
            "action": frame.get("action"),
            "drift": frame.get("quantum", {}).get("drift"),
            "depth": frame.get("stack_hint", 0)
        })
    
    return analysis


def trace_reasoning_path() -> Dict[str, Any]:
    """
    Trace the reasoning path from current state back through history.
    
    Returns:
        Reasoning trace
    """
    print("[🧠] Tracing reasoning path...")
    
    # Get recent history
    history = analyze_history(limit=5)
    
    if not history:
        print("[!] No history available")
        return {"path": [], "depth": 0}
    
    # Analyze progression
    path = []
    for i, frame in enumerate(history):
        path.append({
            "step": len(history) - i,
            "timestamp": frame["timestamp"],
            "state": {
                "goal": frame["goal"],
                "action": frame["action"],
                "drift": frame["drift"]
            },
            "depth": frame["depth"]
        })
    
    print(f"[🧠] Traced {len(path)} reasoning steps")
    
    return {
        "path": path,
        "depth": max(f["depth"] for f in history) if history else 0,
        "pattern": _detect_pattern(history)
    }


def _detect_pattern(history: List[Dict[str, Any]]) -> str:
    """
    Detect patterns in reasoning history.
    
    Args:
        history: List of historical frames
        
    Returns:
        Pattern description
    """
    if not history:
        return "no_data"
    
    # Check for recursion
    depths = [f["depth"] for f in history]
    if all(d > 0 for d in depths):
        if depths[0] > depths[-1]:
            return "recursive_descent"
        elif depths[0] < depths[-1]:
            return "recursive_ascent"
        else:
            return "recursive_stable"
    
    # Check for oscillation
    actions = [f["action"] for f in history]
    if len(set(actions)) <= 2 and len(actions) > 2:
        return "oscillating"
    
    return "normal"


def generate_introspection_report() -> str:
    """
    Generate a comprehensive introspection report.
    
    Returns:
        Report text
    """
    print("\n" + "="*60)
    print("Introspection Report")
    print("="*60 + "\n")
    
    # Capture current state
    current = capture_state()
    
    # Analyze history
    history = analyze_history(limit=10)
    
    # Trace reasoning
    reasoning = trace_reasoning_path()
    
    # Generate report
    report = []
    report.append("Current State:")
    report.append(f"  Goal: {current['goal']}")
    report.append(f"  Action: {current['action']}")
    report.append(f"  Depth: {current['stack_hint']}")
    
    if current.get("quantum"):
        report.append(f"  Drift: {current['quantum'].get('drift', 'N/A')}")
        report.append(f"  Coherence: {current['quantum'].get('coherence', 'N/A')}")
    
    report.append(f"\nHistorical Frames: {len(history)}")
    report.append(f"Reasoning Depth: {reasoning['depth']}")
    report.append(f"Pattern Detected: {reasoning['pattern']}")
    
    if reasoning['path']:
        report.append("\nReasoning Path:")
        for step in reasoning['path'][:5]:  # Show last 5 steps
            report.append(f"  Step {step['step']}: {step['state']['action']} (depth={step['depth']})")
    
    report_text = "\n".join(report)
    print(report_text)
    print("\n" + "="*60 + "\n")
    
    return report_text


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        generate_introspection_report()
    elif len(sys.argv) > 1 and sys.argv[1] == "--trace":
        trace = trace_reasoning_path()
        print(json.dumps(trace, indent=2))
    else:
        # Default: capture current state
        frame = capture_state()
        print(json.dumps(frame, indent=2))
