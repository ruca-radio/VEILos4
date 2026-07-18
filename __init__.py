"""VEILos package exports."""

from .veil_core import VeilKernel, execute_command, get_kernel, main
from .src.runtime_integration import ensure_runtime_integration

__all__ = [
    "VeilKernel",
    "execute_command",
    "get_kernel",
    "main",
    "ensure_runtime_integration",
]
