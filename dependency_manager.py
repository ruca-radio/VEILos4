import subprocess
import sys
import importlib
import os

class DependencyManager:
    def __init__(self):
        self.required_packages = {
            'cryptography': 'cryptography',
            'requests': 'requests',
            'yaml': 'pyyaml'
        }
        self.optional_packages = {
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn',
            'anthropic': 'anthropic',
            'openai': 'openai'
        }

    def check_dependency(self, module_name, package_name=None):
        """Check if a module is available."""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def install_package(self, package_name):
        """Install a package using pip."""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def check_and_install_required(self):
        """Check and install required dependencies."""
        missing = []
        for module, package in self.required_packages.items():
            if not self.check_dependency(module):
                print(f"[!] Missing required package: {package}")
                if self.install_package(package):
                    print(f"[✓] Installed {package}")
                else:
                    missing.append(package)

        if missing:
            print(f"\n[ERROR] Failed to install: {', '.join(missing)}")
            print("Please install manually with: pip install " + " ".join(missing))
            return False
        return True

    def check_optional(self):
        """Check optional dependencies and report status."""
        status = {}
        for module, package in self.optional_packages.items():
            status[package] = self.check_dependency(module)
        return status

# Auto-run when imported
if __name__ == "__main__":
    dm = DependencyManager()
    if dm.check_and_install_required():
        print("[✓] All required dependencies satisfied")

    optional = dm.check_optional()
    print("\nOptional packages:")
    for pkg, available in optional.items():
        print(f"  {pkg}: {'Available' if available else 'Not installed'}")
