"""
Thread Manager
==============
Orchestrates pseudo-parallel agents (LLM interprets as multitask context).
"""

import yaml
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List


THREADS_PATH = "threads/"


def load_thread_spec(thread_file: str) -> Dict[str, Any]:
    """
    Load a thread specification from YAML.
    
    Args:
        thread_file: Thread spec filename
        
    Returns:
        Thread specification dict
    """
    thread_path = Path(THREADS_PATH) / thread_file
    
    with open(thread_path, 'r') as f:
        return yaml.safe_load(f)


def run_thread(thread_file: str) -> Dict[str, Any]:
    """
    Execute a thread by running its command sequence.
    
    Args:
        thread_file: Thread spec filename (e.g., "quantum_supervisor.thread.yaml")
        
    Returns:
        Thread execution results
    """
    print(f"\n{'='*60}")
    print(f"Thread Manager: Launching {thread_file}")
    print(f"{'='*60}")
    
    # Load thread specification
    spec = load_thread_spec(thread_file)
    
    thread_name = spec.get("name", "unknown")
    priority = spec.get("priority", 0)
    sequence = spec.get("sequence", [])
    
    print(f"[↯] Thread: {thread_name} (Priority: {priority})")
    print(f"[↯] Commands: {len(sequence)}")
    print()
    
    results = []
    
    # Execute each command in sequence
    for i, action in enumerate(sequence, 1):
        print(f"[{i}/{len(sequence)}] Executing: {action}")
        
        cmd = ["python3", "veil_core.py"] + action.split()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            results.append({
                "command": action,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            })
            
            # Print output
            if result.stdout:
                print(result.stdout.strip())
            
            if result.returncode != 0:
                print(f"[!] Command failed with code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
        
        except Exception as e:
            print(f"[✗] Exception: {e}")
            results.append({
                "command": action,
                "success": False,
                "error": str(e)
            })
        
        print()
    
    print(f"[✓] Thread {thread_name} complete")
    print(f"{'='*60}\n")
    
    return {
        "thread": thread_name,
        "priority": priority,
        "commands_executed": len(results),
        "results": results
    }


def run_parallel_threads(thread_files: List[str]) -> List[Dict[str, Any]]:
    """
    Run multiple threads in simulated parallel (sequential with priority).
    
    Args:
        thread_files: List of thread spec files
        
    Returns:
        List of execution results
    """
    print("\n" + "="*60)
    print("Thread Manager: Parallel Execution Mode")
    print("="*60)
    
    # Load all specs and sort by priority
    threads = []
    for thread_file in thread_files:
        spec = load_thread_spec(thread_file)
        spec["_file"] = thread_file
        threads.append(spec)
    
    # Sort by priority (higher priority first)
    threads.sort(key=lambda t: t.get("priority", 0), reverse=True)
    
    print(f"\nExecution Order (by priority):")
    for i, thread in enumerate(threads, 1):
        print(f"  {i}. {thread['name']} (priority: {thread.get('priority', 0)})")
    print()
    
    # Execute in priority order
    results = []
    for thread in threads:
        result = run_thread(thread["_file"])
        results.append(result)
    
    return results


def list_threads() -> List[str]:
    """
    List all available thread specifications.
    
    Returns:
        List of thread spec filenames
    """
    threads_dir = Path(THREADS_PATH)
    
    if not threads_dir.exists():
        return []
    
    return [f.name for f in threads_dir.glob("*.thread.yaml")]


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Thread Manager - Usage:")
        print("  python thread_manager.py <thread.yaml>")
        print("  python thread_manager.py --list")
        print("  python thread_manager.py --parallel thread1.yaml thread2.yaml ...")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        threads = list_threads()
        print(f"Available threads ({len(threads)}):")
        for thread in threads:
            print(f"  - {thread}")
    
    elif sys.argv[1] == "--parallel":
        if len(sys.argv) < 3:
            print("Error: --parallel requires at least one thread file")
            sys.exit(1)
        
        thread_files = sys.argv[2:]
        results = run_parallel_threads(thread_files)
        
        print("\nExecution Summary:")
        for result in results:
            print(f"  {result['thread']}: {result['commands_executed']} commands")
    
    else:
        thread_file = sys.argv[1]
        result = run_thread(thread_file)
        print(f"\nThread execution complete: {result['thread']}")
