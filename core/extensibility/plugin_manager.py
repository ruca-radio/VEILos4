"""
VEIL4 Extensibility Framework - Plugin Architecture

Provides a flexible plugin system for extending VEIL4 capabilities.
"""

from typing import Dict, List, Callable, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum
import importlib.util
import sys


class PluginType(Enum):
    """Types of plugins supported by VEIL4"""
    SURFACE = "surface"  # Surface layer plugins
    SECURITY = "security"  # Security/auth plugins
    QUANTUM = "quantum"  # Quantum state management plugins
    AUDIT = "audit"  # Logging/compliance plugins
    COGNITIVE = "cognitive"  # LLM integration plugins


@dataclass
class HookPoint:
    """Defines an extension point in the system"""
    name: str
    hook_type: str  # "filter", "action", "validator"
    description: str
    parameters: Dict[str, Type]
    return_type: Optional[Type] = None


class Plugin:
    """
    Base class for VEIL4 plugins.
    
    All plugins must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = True
        
    def get_name(self) -> str:
        """Return plugin name"""
        raise NotImplementedError
    
    def get_version(self) -> str:
        """Return plugin version"""
        raise NotImplementedError
    
    def get_type(self) -> PluginType:
        """Return plugin type"""
        raise NotImplementedError
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        return True
    
    def shutdown(self):
        """Cleanup when plugin is unloaded"""
        pass
    
    def get_hooks(self) -> Dict[str, Callable]:
        """
        Return dictionary of hook implementations.
        
        Returns:
            Dict mapping hook names to implementation functions
        """
        return {}


class PluginManager:
    """
    Manages the plugin system for VEIL4.
    
    Handles plugin loading, initialization, and hook execution.
    """
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[tuple[int, Callable]]] = {}  # hook_name -> [(priority, func)]
        self.hook_registry: Dict[str, HookPoint] = {}
        
    def register_hook_point(self, hook: HookPoint):
        """Register a new hook point in the system"""
        self.hook_registry[hook.name] = hook
        if hook.name not in self.hooks:
            self.hooks[hook.name] = []
    
    def load_plugin(self, plugin: Plugin, priority: int = 50) -> bool:
        """
        Load and initialize a plugin.
        
        Args:
            plugin: Plugin instance to load
            priority: Execution priority (lower = earlier, 0-100)
            
        Returns:
            True if plugin loaded successfully
        """
        name = plugin.get_name()
        
        # Check if already loaded
        if name in self.plugins:
            return False
        
        # Initialize plugin
        if not plugin.initialize():
            return False
        
        # Register plugin
        self.plugins[name] = plugin
        
        # Register hooks
        hooks = plugin.get_hooks()
        for hook_name, hook_func in hooks.items():
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            self.hooks[hook_name].append((priority, hook_func))
            # Sort by priority
            self.hooks[hook_name].sort(key=lambda x: x[0])
        
        return True
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if plugin unloaded successfully
        """
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Remove hooks
        hooks = plugin.get_hooks()
        for hook_name in hooks:
            if hook_name in self.hooks:
                self.hooks[hook_name] = [
                    (p, f) for p, f in self.hooks[hook_name]
                    if f != hooks[hook_name]
                ]
        
        # Shutdown plugin
        plugin.shutdown()
        
        # Remove from registry
        del self.plugins[plugin_name]
        
        return True
    
    def execute_hook(
        self,
        hook_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute all functions registered for a hook.
        
        For filters: each function's output becomes the next function's input
        For actions: all functions are called with the same arguments
        
        Args:
            hook_name: Name of the hook to execute
            *args, **kwargs: Arguments to pass to hook functions
            
        Returns:
            Result depends on hook type
        """
        if hook_name not in self.hooks:
            return args[0] if args else None
        
        if hook_name not in self.hook_registry:
            # Unknown hook, execute as action
            for _, func in self.hooks[hook_name]:
                func(*args, **kwargs)
            return None
        
        hook_point = self.hook_registry[hook_name]
        
        if hook_point.hook_type == "filter":
            # Filters modify and pass data through
            result = args[0] if args else None
            for _, func in self.hooks[hook_name]:
                result = func(result, *args[1:], **kwargs)
            return result
            
        elif hook_point.hook_type == "validator":
            # Validators must all return True
            for _, func in self.hooks[hook_name]:
                if not func(*args, **kwargs):
                    return False
            return True
            
        else:  # action
            # Actions are just called
            for _, func in self.hooks[hook_name]:
                func(*args, **kwargs)
            return None
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[str]:
        """
        List all loaded plugins.
        
        Args:
            plugin_type: Filter by plugin type (None = all)
            
        Returns:
            List of plugin names
        """
        if plugin_type is None:
            return list(self.plugins.keys())
        
        return [
            name for name, plugin in self.plugins.items()
            if plugin.get_type() == plugin_type
        ]
    
    def load_plugin_from_file(
        self,
        filepath: str,
        class_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Dynamically load a plugin from a Python file.
        
        Args:
            filepath: Path to plugin file
            class_name: Name of plugin class to instantiate
            config: Configuration to pass to plugin
            
        Returns:
            True if plugin loaded successfully
        """
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location("dynamic_plugin", filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules["dynamic_plugin"] = module
                spec.loader.exec_module(module)
                
                # Get plugin class
                plugin_class = getattr(module, class_name)
                
                # Instantiate and load
                plugin = plugin_class(config)
                return self.load_plugin(plugin)
                
        except Exception as e:
            print(f"Failed to load plugin from {filepath}: {e}")
            return False
        
        return False
