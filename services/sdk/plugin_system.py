"""
Plugin System

This module provides the core plugin system for the Code Deep Dive Analyzer platform,
allowing third-party developers to extend the system's functionality.
"""
import os
import sys
import json
import logging
import importlib
import inspect
import uuid
import time
from typing import Dict, List, Any, Optional, Union, Callable, Type, Set
from abc import ABC, abstractmethod

class PluginMetadata:
    """Metadata for a plugin."""
    def __init__(self, 
                id: str,
                name: str, 
                version: str,
                description: str,
                author: str,
                entry_point: str,
                dependencies: Optional[List[str]] = None,
                capabilities: Optional[List[str]] = None,
                configuration_schema: Optional[Dict[str, Any]] = None,
                min_platform_version: Optional[str] = None):
        """
        Initialize plugin metadata.
        
        Args:
            id: Unique identifier for the plugin
            name: Human-readable name
            version: Version string (semver)
            description: Description of the plugin
            author: Author information
            entry_point: Module.Class entry point
            dependencies: Optional list of dependency plugins
            capabilities: Optional list of capabilities provided
            configuration_schema: Optional JSON schema for configuration
            min_platform_version: Minimum required platform version
        """
        self.id = id
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.entry_point = entry_point
        self.dependencies = dependencies or []
        self.capabilities = capabilities or []
        self.configuration_schema = configuration_schema or {}
        self.min_platform_version = min_platform_version or "1.0.0"
        self.install_time = time.time()
        self.last_loaded = None
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PluginMetadata':
        """Create metadata from a dictionary."""
        return PluginMetadata(
            id=data.get('id', str(uuid.uuid4())),
            name=data['name'],
            version=data['version'],
            description=data['description'],
            author=data['author'],
            entry_point=data['entry_point'],
            dependencies=data.get('dependencies'),
            capabilities=data.get('capabilities'),
            configuration_schema=data.get('configuration_schema'),
            min_platform_version=data.get('min_platform_version')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'entry_point': self.entry_point,
            'dependencies': self.dependencies,
            'capabilities': self.capabilities,
            'configuration_schema': self.configuration_schema,
            'min_platform_version': self.min_platform_version,
            'install_time': self.install_time,
            'last_loaded': self.last_loaded
        }


class PluginInterface(ABC):
    """
    Base interface that all plugins must implement.
    
    This defines the lifecycle methods that the plugin system will call.
    """
    
    @abstractmethod
    def initialize(self, context: 'PluginContext') -> bool:
        """
        Initialize the plugin.
        
        Args:
            context: Plugin context providing access to platform services
            
        Returns:
            Initialization success
        """
        pass
    
    @abstractmethod
    def activate(self) -> bool:
        """
        Activate the plugin.
        
        Returns:
            Activation success
        """
        pass
    
    @abstractmethod
    def deactivate(self) -> bool:
        """
        Deactivate the plugin.
        
        Returns:
            Deactivation success
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get the capabilities provided by this plugin.
        
        Returns:
            List of capability identifiers
        """
        pass


class PluginContext:
    """
    Context provided to plugins during initialization.
    
    This gives plugins access to platform services and APIs.
    """
    
    def __init__(self, 
                service_registry: Dict[str, Any],
                configuration: Dict[str, Any],
                logger: logging.Logger,
                plugin_manager: 'PluginManager',
                metadata: PluginMetadata):
        """
        Initialize plugin context.
        
        Args:
            service_registry: Registry of platform services
            configuration: Plugin configuration
            logger: Logger instance for the plugin
            plugin_manager: Reference to the plugin manager
            metadata: Plugin metadata
        """
        self.service_registry = service_registry
        self.configuration = configuration
        self.logger = logger
        self.plugin_manager = plugin_manager
        self.metadata = metadata
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a platform service by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None if not found
        """
        return self.service_registry.get(service_name)
    
    def get_configuration(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get plugin configuration.
        
        Args:
            key: Optional specific configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or entire configuration
        """
        if key is None:
            return self.configuration
        
        return self.configuration.get(key, default)
    
    def get_plugin(self, plugin_id: str) -> Optional['PluginInstance']:
        """
        Get another plugin by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugin_manager.get_plugin(plugin_id)


class ExtensionPoint:
    """
    Extension point that plugins can implement.
    
    This provides a way for plugins to register handlers for specific extension points.
    """
    
    def __init__(self, name: str, description: str, interface: Type):
        """
        Initialize extension point.
        
        Args:
            name: Name of the extension point
            description: Description of the extension point
            interface: Interface that handlers must implement
        """
        self.name = name
        self.description = description
        self.interface = interface
        self.handlers = {}
    
    def register_handler(self, plugin_id: str, handler: Any) -> bool:
        """
        Register a handler for this extension point.
        
        Args:
            plugin_id: ID of the plugin providing the handler
            handler: Handler implementation
            
        Returns:
            Registration success
        """
        # Validate handler against interface
        if not isinstance(handler, self.interface):
            return False
        
        self.handlers[plugin_id] = handler
        return True
    
    def unregister_handler(self, plugin_id: str) -> bool:
        """
        Unregister a handler.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Unregistration success
        """
        if plugin_id in self.handlers:
            del self.handlers[plugin_id]
            return True
        
        return False
    
    def get_handlers(self) -> List[Any]:
        """
        Get all registered handlers.
        
        Returns:
            List of handlers
        """
        return list(self.handlers.values())


class PluginInstance:
    """
    Represents a loaded plugin instance.
    
    This wraps the actual plugin implementation and provides lifecycle management.
    """
    
    def __init__(self, 
                metadata: PluginMetadata,
                instance: PluginInterface,
                context: PluginContext):
        """
        Initialize plugin instance.
        
        Args:
            metadata: Plugin metadata
            instance: Actual plugin implementation
            context: Plugin context
        """
        self.metadata = metadata
        self.instance = instance
        self.context = context
        self.active = False
        self.error = None
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            Initialization success
        """
        try:
            result = self.instance.initialize(self.context)
            if result:
                self.context.logger.info(f"Plugin '{self.metadata.name}' initialized successfully")
            else:
                self.context.logger.error(f"Plugin '{self.metadata.name}' initialization returned False")
                self.error = "Initialization failed"
            
            return result
        except Exception as e:
            self.context.logger.error(f"Error initializing plugin '{self.metadata.name}': {str(e)}")
            self.error = str(e)
            return False
    
    def activate(self) -> bool:
        """
        Activate the plugin.
        
        Returns:
            Activation success
        """
        if self.active:
            return True
        
        try:
            result = self.instance.activate()
            if result:
                self.active = True
                self.context.logger.info(f"Plugin '{self.metadata.name}' activated successfully")
            else:
                self.context.logger.error(f"Plugin '{self.metadata.name}' activation returned False")
                self.error = "Activation failed"
            
            return result
        except Exception as e:
            self.context.logger.error(f"Error activating plugin '{self.metadata.name}': {str(e)}")
            self.error = str(e)
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the plugin.
        
        Returns:
            Deactivation success
        """
        if not self.active:
            return True
        
        try:
            result = self.instance.deactivate()
            if result:
                self.active = False
                self.context.logger.info(f"Plugin '{self.metadata.name}' deactivated successfully")
            else:
                self.context.logger.error(f"Plugin '{self.metadata.name}' deactivation returned False")
            
            return result
        except Exception as e:
            self.context.logger.error(f"Error deactivating plugin '{self.metadata.name}': {str(e)}")
            # Don't set error here, as we might want to force deactivation even with errors
            return False
    
    def is_active(self) -> bool:
        """
        Check if the plugin is active.
        
        Returns:
            Active status
        """
        return self.active
    
    def get_capabilities(self) -> List[str]:
        """
        Get plugin capabilities.
        
        Returns:
            List of capabilities
        """
        return self.instance.get_capabilities()


class PluginManager:
    """
    Plugin manager for loading, activating, and managing plugins.
    
    This is the central component of the plugin system.
    """
    
    def __init__(self, plugin_dirs: List[str], service_registry: Dict[str, Any]):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins
            service_registry: Registry of platform services
        """
        self.plugin_dirs = plugin_dirs
        self.service_registry = service_registry
        self.plugins = {}  # plugin_id -> PluginInstance
        self.metadata_cache = {}  # plugin_id -> PluginMetadata
        self.extension_points = {}  # extension_point_name -> ExtensionPoint
        self.logger = logging.getLogger('plugin_manager')
        
        # Create plugin directories if they don't exist
        for plugin_dir in plugin_dirs:
            os.makedirs(plugin_dir, exist_ok=True)
        
        # Load plugin metadata
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load metadata for all available plugins."""
        self.metadata_cache = {}
        
        for plugin_dir in self.plugin_dirs:
            # Look for plugin.json files
            for entry in os.listdir(plugin_dir):
                entry_path = os.path.join(plugin_dir, entry)
                
                if os.path.isdir(entry_path):
                    metadata_path = os.path.join(entry_path, 'plugin.json')
                    
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r') as f:
                                data = json.load(f)
                                
                                metadata = PluginMetadata.from_dict(data)
                                self.metadata_cache[metadata.id] = metadata
                                
                                self.logger.info(f"Found plugin: {metadata.name} (ID: {metadata.id}, Version: {metadata.version})")
                        except Exception as e:
                            self.logger.error(f"Error loading plugin metadata from {metadata_path}: {str(e)}")
    
    def register_extension_point(self, name: str, description: str, interface: Type) -> ExtensionPoint:
        """
        Register a new extension point.
        
        Args:
            name: Name of the extension point
            description: Description of the extension point
            interface: Interface that handlers must implement
            
        Returns:
            Created extension point
        """
        if name in self.extension_points:
            raise ValueError(f"Extension point '{name}' already exists")
        
        extension_point = ExtensionPoint(name, description, interface)
        self.extension_points[name] = extension_point
        
        self.logger.info(f"Registered extension point: {name}")
        return extension_point
    
    def get_extension_point(self, name: str) -> Optional[ExtensionPoint]:
        """
        Get an extension point by name.
        
        Args:
            name: Name of the extension point
            
        Returns:
            Extension point or None if not found
        """
        return self.extension_points.get(name)
    
    def register_extension(self, extension_point_name: str, plugin_id: str, handler: Any) -> bool:
        """
        Register an extension handler.
        
        Args:
            extension_point_name: Name of the extension point
            plugin_id: ID of the plugin providing the handler
            handler: Handler implementation
            
        Returns:
            Registration success
        """
        extension_point = self.get_extension_point(extension_point_name)
        if not extension_point:
            self.logger.error(f"Extension point '{extension_point_name}' not found")
            return False
        
        result = extension_point.register_handler(plugin_id, handler)
        if result:
            self.logger.info(f"Registered handler for extension point '{extension_point_name}' from plugin '{plugin_id}'")
        else:
            self.logger.error(f"Failed to register handler for extension point '{extension_point_name}' from plugin '{plugin_id}'")
        
        return result
    
    def load_plugin(self, plugin_id: str, config: Optional[Dict[str, Any]] = None) -> Optional[PluginInstance]:
        """
        Load a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to load
            config: Optional plugin configuration
            
        Returns:
            Loaded plugin instance or None if loading failed
        """
        # Check if plugin is already loaded
        if plugin_id in self.plugins:
            self.logger.info(f"Plugin '{plugin_id}' is already loaded")
            return self.plugins[plugin_id]
        
        # Check if metadata exists
        if plugin_id not in self.metadata_cache:
            self.logger.error(f"No metadata found for plugin '{plugin_id}'")
            return None
        
        metadata = self.metadata_cache[plugin_id]
        
        # Check dependencies
        for dep_id in metadata.dependencies:
            if dep_id not in self.plugins:
                # Try to load the dependency
                dep_instance = self.load_plugin(dep_id)
                if not dep_instance:
                    self.logger.error(f"Cannot load plugin '{plugin_id}' because dependency '{dep_id}' failed to load")
                    return None
        
        try:
            # Parse entry point
            module_name, class_name = metadata.entry_point.rsplit('.', 1)
            
            # Add plugin directory to Python path
            for plugin_dir in self.plugin_dirs:
                plugin_path = os.path.join(plugin_dir, metadata.name)
                if os.path.exists(plugin_path):
                    if plugin_path not in sys.path:
                        sys.path.append(plugin_path)
                    break
            
            # Import the module
            module = importlib.import_module(module_name)
            
            # Get the plugin class
            plugin_class = getattr(module, class_name)
            
            # Create plugin instance
            plugin_instance = plugin_class()
            
            # Create plugin logger
            plugin_logger = logging.getLogger(f'plugin.{metadata.name}')
            
            # Create plugin context
            plugin_context = PluginContext(
                service_registry=self.service_registry,
                configuration=config or {},
                logger=plugin_logger,
                plugin_manager=self,
                metadata=metadata
            )
            
            # Create plugin wrapper
            instance = PluginInstance(
                metadata=metadata,
                instance=plugin_instance,
                context=plugin_context
            )
            
            # Initialize the plugin
            if not instance.initialize():
                self.logger.error(f"Plugin '{metadata.name}' failed to initialize")
                return None
            
            # Update metadata
            metadata.last_loaded = time.time()
            
            # Store the instance
            self.plugins[plugin_id] = instance
            
            self.logger.info(f"Loaded plugin: {metadata.name} (ID: {plugin_id})")
            return instance
        except Exception as e:
            self.logger.error(f"Error loading plugin '{plugin_id}': {str(e)}")
            return None
    
    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a plugin.
        
        Args:
            plugin_id: ID of the plugin to activate
            
        Returns:
            Activation success
        """
        if plugin_id not in self.plugins:
            self.logger.error(f"Cannot activate plugin '{plugin_id}' because it is not loaded")
            return False
        
        instance = self.plugins[plugin_id]
        
        # Check if already active
        if instance.is_active():
            return True
        
        # Activate dependencies first
        metadata = instance.metadata
        for dep_id in metadata.dependencies:
            if not self.activate_plugin(dep_id):
                self.logger.error(f"Cannot activate plugin '{plugin_id}' because dependency '{dep_id}' failed to activate")
                return False
        
        # Activate the plugin
        result = instance.activate()
        
        if result:
            self.logger.info(f"Activated plugin: {metadata.name} (ID: {plugin_id})")
        
        return result
    
    def deactivate_plugin(self, plugin_id: str, force: bool = False) -> bool:
        """
        Deactivate a plugin.
        
        Args:
            plugin_id: ID of the plugin to deactivate
            force: Force deactivation even if dependencies exist
            
        Returns:
            Deactivation success
        """
        if plugin_id not in self.plugins:
            self.logger.error(f"Cannot deactivate plugin '{plugin_id}' because it is not loaded")
            return False
        
        instance = self.plugins[plugin_id]
        
        # Check if already inactive
        if not instance.is_active():
            return True
        
        # Check for dependents
        if not force:
            dependents = self._find_dependents(plugin_id)
            if dependents:
                active_dependents = [dep_id for dep_id in dependents if self.plugins[dep_id].is_active()]
                if active_dependents:
                    self.logger.error(f"Cannot deactivate plugin '{plugin_id}' because it has active dependents: {', '.join(active_dependents)}")
                    return False
        
        # Deactivate the plugin
        result = instance.deactivate()
        
        if result:
            self.logger.info(f"Deactivated plugin: {instance.metadata.name} (ID: {plugin_id})")
        
        return result
    
    def _find_dependents(self, plugin_id: str) -> List[str]:
        """
        Find plugins that depend on a given plugin.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            List of dependent plugin IDs
        """
        dependents = []
        
        for other_id, instance in self.plugins.items():
            if plugin_id in instance.metadata.dependencies:
                dependents.append(other_id)
        
        return dependents
    
    def unload_plugin(self, plugin_id: str, force: bool = False) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_id: ID of the plugin to unload
            force: Force unloading even if dependencies exist
            
        Returns:
            Unloading success
        """
        if plugin_id not in self.plugins:
            self.logger.error(f"Cannot unload plugin '{plugin_id}' because it is not loaded")
            return False
        
        instance = self.plugins[plugin_id]
        
        # Deactivate if active
        if instance.is_active():
            if not self.deactivate_plugin(plugin_id, force):
                return False
        
        # Check for dependents
        if not force:
            dependents = self._find_dependents(plugin_id)
            if dependents:
                self.logger.error(f"Cannot unload plugin '{plugin_id}' because it has dependents: {', '.join(dependents)}")
                return False
        
        # Remove from extension points
        for extension_point in self.extension_points.values():
            extension_point.unregister_handler(plugin_id)
        
        # Remove the instance
        del self.plugins[plugin_id]
        
        self.logger.info(f"Unloaded plugin: {instance.metadata.name} (ID: {plugin_id})")
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInstance]:
        """
        Get a plugin by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_id)
    
    def get_plugins_by_capability(self, capability: str) -> List[PluginInstance]:
        """
        Get plugins that provide a specific capability.
        
        Args:
            capability: Capability identifier
            
        Returns:
            List of plugin instances
        """
        result = []
        
        for instance in self.plugins.values():
            if capability in instance.get_capabilities():
                result.append(instance)
        
        return result
    
    def get_active_plugins(self) -> List[PluginInstance]:
        """
        Get all active plugins.
        
        Returns:
            List of active plugin instances
        """
        return [instance for instance in self.plugins.values() if instance.is_active()]
    
    def get_plugin_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """
        Get metadata for a plugin.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin metadata or None if not found
        """
        # Check loaded plugins first
        if plugin_id in self.plugins:
            return self.plugins[plugin_id].metadata
        
        # Check metadata cache
        return self.metadata_cache.get(plugin_id)
    
    def get_available_plugins(self) -> List[PluginMetadata]:
        """
        Get metadata for all available plugins.
        
        Returns:
            List of plugin metadata
        """
        return list(self.metadata_cache.values())
    
    def refresh_metadata(self) -> None:
        """Refresh the plugin metadata cache."""
        self._load_metadata()
        self.logger.info("Refreshed plugin metadata cache")


class PluginSDK:
    """
    SDK for plugin developers.
    
    This provides utilities for plugin development and testing.
    """
    
    @staticmethod
    def create_plugin_structure(output_dir: str, metadata: Dict[str, Any]) -> str:
        """
        Create a basic plugin structure.
        
        Args:
            output_dir: Directory to create the plugin in
            metadata: Plugin metadata
            
        Returns:
            Path to the created plugin directory
        """
        name = metadata['name']
        plugin_dir = os.path.join(output_dir, name)
        
        # Create plugin directory
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Create metadata file
        with open(os.path.join(plugin_dir, 'plugin.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create Python package
        os.makedirs(os.path.join(plugin_dir, name), exist_ok=True)
        
        # Create __init__.py
        with open(os.path.join(plugin_dir, name, '__init__.py'), 'w') as f:
            f.write(f'"""Plugin package for {name}."""\n')
        
        # Extract class name from entry point
        module_name, class_name = metadata['entry_point'].rsplit('.', 1)
        
        # Create main plugin file
        plugin_file = os.path.join(plugin_dir, name, 'plugin.py')
        with open(plugin_file, 'w') as f:
            f.write(f'''"""
{name} Plugin

{metadata['description']}
"""
from typing import List, Dict, Any, Optional

class {class_name}:
    """
    {name} plugin implementation.
    """
    
    def initialize(self, context):
        """
        Initialize the plugin.
        
        Args:
            context: Plugin context
            
        Returns:
            Initialization success
        """
        self.context = context
        self.logger = context.logger
        
        self.logger.info("{name} plugin initialized")
        return True
    
    def activate(self):
        """
        Activate the plugin.
        
        Returns:
            Activation success
        """
        self.logger.info("{name} plugin activated")
        return True
    
    def deactivate(self):
        """
        Deactivate the plugin.
        
        Returns:
            Deactivation success
        """
        self.logger.info("{name} plugin deactivated")
        return True
    
    def get_capabilities(self):
        """
        Get plugin capabilities.
        
        Returns:
            List of capabilities
        """
        return {metadata.get('capabilities', [])}
''')
        
        # Create README.md
        with open(os.path.join(plugin_dir, 'README.md'), 'w') as f:
            f.write(f'''# {name}

{metadata['description']}

## Author

{metadata['author']}

## Version

{metadata['version']}

## Installation

1. Copy this directory to the plugins directory of the Code Deep Dive Analyzer.
2. Restart the application.
3. Enable the plugin in the plugin manager.

## Configuration

TODO: Add configuration instructions.

## Usage

TODO: Add usage instructions.
''')
        
        return plugin_dir
    
    @staticmethod
    def validate_plugin(plugin_dir: str) -> Dict[str, Any]:
        """
        Validate a plugin.
        
        Args:
            plugin_dir: Path to the plugin directory
            
        Returns:
            Validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if plugin.json exists
        metadata_path = os.path.join(plugin_dir, 'plugin.json')
        if not os.path.exists(metadata_path):
            results['valid'] = False
            results['errors'].append(f"Missing plugin.json file")
            return results
        
        # Load and validate metadata
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check required fields
            required_fields = ['name', 'version', 'description', 'author', 'entry_point']
            for field in required_fields:
                if field not in metadata:
                    results['valid'] = False
                    results['errors'].append(f"Missing required field in plugin.json: {field}")
            
            # Parse entry point
            if 'entry_point' in metadata:
                try:
                    module_name, class_name = metadata['entry_point'].rsplit('.', 1)
                    
                    # Check if the module exists
                    sys.path.append(plugin_dir)
                    try:
                        module = importlib.import_module(module_name)
                        
                        # Check if the class exists
                        if not hasattr(module, class_name):
                            results['valid'] = False
                            results['errors'].append(f"Entry point class '{class_name}' not found in module '{module_name}'")
                        else:
                            # Check if the class implements the required methods
                            plugin_class = getattr(module, class_name)
                            
                            required_methods = ['initialize', 'activate', 'deactivate', 'get_capabilities']
                            for method in required_methods:
                                if not hasattr(plugin_class, method):
                                    results['valid'] = False
                                    results['errors'].append(f"Plugin class is missing required method: {method}")
                    except ImportError as e:
                        results['valid'] = False
                        results['errors'].append(f"Failed to import plugin module '{module_name}': {str(e)}")
                    finally:
                        if plugin_dir in sys.path:
                            sys.path.remove(plugin_dir)
                except ValueError:
                    results['valid'] = False
                    results['errors'].append(f"Invalid entry point format: {metadata['entry_point']}")
        
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Error loading plugin.json: {str(e)}")
        
        return results


# Define some commonly used extension point interfaces

class CodeAnalyzerExtension(ABC):
    """Interface for code analyzer extensions."""
    
    @abstractmethod
    def analyze_code(self, code: str, language: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code.
        
        Args:
            code: Source code to analyze
            language: Programming language of the code
            options: Analysis options
            
        Returns:
            Analysis results
        """
        pass


class VisualizationExtension(ABC):
    """Interface for visualization extensions."""
    
    @abstractmethod
    def generate_visualization(self, data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate visualization.
        
        Args:
            data: Data to visualize
            options: Visualization options
            
        Returns:
            Visualization results
        """
        pass


class ModelProviderExtension(ABC):
    """Interface for model provider extensions."""
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get available models.
        
        Returns:
            List of available models with metadata
        """
        pass
    
    @abstractmethod
    def load_model(self, model_id: str) -> Any:
        """
        Load a model.
        
        Args:
            model_id: ID of the model to load
            
        Returns:
            Loaded model
        """
        pass
    
    @abstractmethod
    def infer(self, model: Any, input_data: Any) -> Any:
        """
        Perform inference with a model.
        
        Args:
            model: Loaded model
            input_data: Input data for inference
            
        Returns:
            Inference result
        """
        pass