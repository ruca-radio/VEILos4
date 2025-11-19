#!/usr/bin/env python3
"""
VEILed - VEILos Daemon
======================
Simulates always-on VEIL thread that runs background tasks.
Daemon mode for continuous loop execution.
"""

import time
import sys
import os

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

import loop_manager


def daemon_loop(interval=3, max_iterations=None):
    """
    Main daemon loop.
    
    Args:
        interval: Seconds between loop iterations
        max_iterations: Max iterations (None = infinite)
    """
    print("[~] VEILos Daemon started.")
    print(f"[~] Loop interval: {interval}s")
    
    if max_iterations:
        print(f"[~] Max iterations: {max_iterations}")
    else:
        print("[~] Running indefinitely (Ctrl+C to stop)")
    
    print()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"[Daemon] Iteration {iteration} @ {time.strftime('%H:%M:%S')}")
            
            # Execute loop manager
            result = loop_manager.run()
            
            # Check if we should continue
            if result.get("status") == "limit_reached":
                print("[!] Loop manager reached recursion limit. Stopping daemon.")
                break
            
            if max_iterations and iteration >= max_iterations:
                print(f"[~] Reached max iterations ({max_iterations}). Stopping daemon.")
                break
            
            # Sleep until next iteration
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n[~] Daemon stopped by user (Ctrl+C)")
    
    print("[~] VEILos Daemon shutdown complete.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VEILos Daemon - Background task server")
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="Seconds between loop iterations (default: 3)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum iterations (default: infinite)"
    )
    
    args = parser.parse_args()
    
    daemon_loop(interval=args.interval, max_iterations=args.max_iterations)


if __name__ == "__main__":
    main()
