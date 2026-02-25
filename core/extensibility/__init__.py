"""VEIL4 Core Extensibility Module"""

from .plugin_manager import PluginManager, Plugin, PluginType, HookPoint

__all__ = [
    'PluginManager',
    'Plugin',
    'PluginType',
    'HookPoint'
]
