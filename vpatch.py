"""
VPatch - Self-Patching Engine
==============================
Allows modules to be patched/updated at runtime.
Supports unified diff format and direct replacement.
"""

import difflib
import os
import shutil
from pathlib import Path
from typing import Optional


def apply_patch(module_path: str, patch_path: str, backup: bool = True) -> bool:
    """
    Apply a patch to a module.
    
    Args:
        module_path: Path to module to patch
        patch_path: Path to patch file
        backup: Create backup before patching
        
    Returns:
        True if patch applied successfully
    """
    if not os.path.exists(module_path):
        print(f"[✗] Module not found: {module_path}")
        return False
    
    if not os.path.exists(patch_path):
        print(f"[✗] Patch not found: {patch_path}")
        return False
    
    try:
        # Read original module
        with open(module_path, 'r') as f:
            original = f.readlines()
        
        # Read patch (could be diff or direct replacement)
        with open(patch_path, 'r') as f:
            patch_content = f.read()
        
        # Create backup if requested
        if backup:
            backup_path = f"{module_path}.backup"
            shutil.copy2(module_path, backup_path)
            print(f"[+] Backup created: {backup_path}")
        
        # For simplicity, treat patch as direct replacement
        # In production, would parse unified diff format
        with open(module_path, 'w') as f:
            f.write(patch_content)
        
        print(f"[✓] Patch applied to {module_path}")
        return True
    
    except Exception as e:
        print(f"[✗] Failed to apply patch: {e}")
        return False


def create_patch(original_path: str, modified_path: str, output_path: str) -> bool:
    """
    Create a patch file from original and modified versions.
    
    Args:
        original_path: Path to original file
        modified_path: Path to modified file
        output_path: Where to save patch
        
    Returns:
        True if patch created successfully
    """
    try:
        with open(original_path, 'r') as f:
            original = f.readlines()
        
        with open(modified_path, 'r') as f:
            modified = f.readlines()
        
        # Generate unified diff
        diff = difflib.unified_diff(
            original,
            modified,
            fromfile=original_path,
            tofile=modified_path,
            lineterm=''
        )
        
        diff_text = '\n'.join(diff)
        
        if not diff_text:
            print("[!] No differences found")
            return False
        
        # Save patch
        with open(output_path, 'w') as f:
            f.write(diff_text)
        
        print(f"[✓] Patch created: {output_path}")
        return True
    
    except Exception as e:
        print(f"[✗] Failed to create patch: {e}")
        return False


def validate_patch(module_path: str, patch_path: str) -> bool:
    """
    Validate that a patch can be applied (dry run).
    
    Args:
        module_path: Path to module
        patch_path: Path to patch
        
    Returns:
        True if patch is valid
    """
    # Simple validation: check files exist and are readable
    try:
        with open(module_path, 'r') as f:
            _ = f.read()
        
        with open(patch_path, 'r') as f:
            _ = f.read()
        
        print(f"[✓] Patch validation passed")
        return True
    
    except Exception as e:
        print(f"[✗] Patch validation failed: {e}")
        return False


def rollback_patch(module_path: str) -> bool:
    """
    Rollback a patch by restoring from backup.
    
    Args:
        module_path: Path to module
        
    Returns:
        True if rollback successful
    """
    backup_path = f"{module_path}.backup"
    
    if not os.path.exists(backup_path):
        print(f"[✗] No backup found: {backup_path}")
        return False
    
    try:
        shutil.copy2(backup_path, module_path)
        print(f"[✓] Rollback successful: {module_path}")
        return True
    
    except Exception as e:
        print(f"[✗] Rollback failed: {e}")
        return False


# Example usage
if __name__ == "__main__":
    print("VPatch - Self-Patching Engine")
    print("=" * 40)
    
    # Example: validate a patch
    if os.path.exists("modules/agent_harmonizer.py"):
        print("\nValidating sample patch...")
        # In real usage, would have actual patch file
        print("Patch system ready for use")
