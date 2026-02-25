"""
Sandbox Patch Runner
====================
Safe execution environment for testing patches before applying to production.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vpatch import apply_patch, validate_patch, rollback_patch


def test_patch(module: str, patch: str):
    """
    Test a patch in sandbox environment.
    
    Args:
        module: Module name (e.g., "agent_harmonizer.py")
        patch: Patch name (e.g., "agent_harmonizer_patch01.vpatch")
    """
    print("=" * 60)
    print("Sandbox Patch Runner")
    print("=" * 60)
    
    module_path = os.path.join("modules", module)
    patch_path = os.path.join("patches", patch)
    
    # Step 1: Validate
    print(f"\n[1] Validating patch...")
    if not validate_patch(module_path, patch_path):
        print("[!] Validation failed. Aborting.")
        return False
    
    # Step 2: Apply
    print(f"\n[2] Applying patch...")
    if not apply_patch(module_path, patch_path, backup=True):
        print("[!] Patch application failed.")
        return False
    
    # Step 3: Test execution
    print(f"\n[3] Testing patched module...")
    try:
        # Import and run the patched module
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        if hasattr(test_module, 'run'):
            result = test_module.run()
            print(f"[✓] Test execution successful")
            print(f"Result: {result}")
        else:
            print("[!] Module has no run() function")
    
    except Exception as e:
        print(f"[✗] Test execution failed: {e}")
        print("\n[4] Rolling back patch...")
        rollback_patch(module_path)
        return False
    
    print("\n[✓] Patch test complete. Module ready for production.")
    print(f"    Backup available at: {module_path}.backup")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sandbox/patch_runner.py <module.py> <patch.vpatch>")
        sys.exit(1)
    
    module = sys.argv[1]
    patch = sys.argv[2]
    
    success = test_patch(module, patch)
    sys.exit(0 if success else 1)
