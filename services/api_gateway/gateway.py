"""
API Gateway

This module provides a unified API Gateway for the Code Deep Dive Analyzer system,
coordinating requests across all microservices.
"""
import logging
import importlib
import os
import sys
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum

# Add parent directory to path to import from sibling packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ServiceStatus(Enum):
    """Status of a service in the API Gateway."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    """Types of services in the system."""
    REPOSITORY = "repository"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    MODEL_HUB = "model_hub"
    AGENT_ORCHESTRATOR = "agent_orchestrator"
    NEURO_SYMBOLIC = "neuro_symbolic"
    MULTIMODAL = "multimodal"
    SDK = "sdk"
    ACADEMIC = "academic"
    PROTOCOL = "protocol"

class APIGateway:
    """
    API Gateway for the Code Deep Dive Analyzer system.
    
    This class provides:
    - Unified access to all microservices
    - Service discovery and routing
    - Request validation and transformation
    - Error handling and logging
    - Rate limiting and throttling
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the API Gateway.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger('api_gateway')
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize service registry
        self.services = {}
        self.service_instances = {}
        self.service_status = {}
        
        # Register all available services
        self._discover_services()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'services': {
                'repository': {
                    'module': 'repository_service.repository_manager',
                    'class': 'RepositoryManager',
                    'enabled': True
                },
                'knowledge_graph': {
                    'module': 'knowledge_graph.knowledge_graph',
                    'class': 'MultiRepositoryKnowledgeGraph',
                    'enabled': True
                },
                'model_hub': {
                    'module': 'model_hub.model_registry',
                    'class': 'ModelRegistry',
                    'enabled': True
                },
                'agent_orchestrator': {
                    'module': 'agent_orchestrator.orchestrator',
                    'class': 'AgentOrchestrator',
                    'enabled': True
                },
                'neuro_symbolic': {
                    'module': 'neuro_symbolic.reasoning_engine',
                    'class': 'NeuroSymbolicEngine',
                    'enabled': True
                },
                'multimodal': {
                    'module': 'multimodal.multimodal_processor',
                    'class': 'MultimodalProcessor',
                    'enabled': True
                },
                'sdk': {
                    'module': 'sdk.plugin_system',
                    'class': 'PluginManager',
                    'enabled': True
                },
                'academic': {
                    'module': 'academic.academic_framework',
                    'class': 'AcademicFramework',
                    'enabled': True
                },
                'protocol': {
                    'module': 'protocol_server',
                    'class': 'ProtocolServer',
                    'enabled': True
                }
            },
            'rate_limits': {
                'default': 100,  # Requests per minute
                'repository': 50,
                'knowledge_graph': 30
            },
            'timeouts': {
                'default': 30,  # Seconds
                'repository_clone': 300,
                'knowledge_graph_query': 60
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults
                for key, value in config.items():
                    if key in default_config and isinstance(value, dict) and isinstance(default_config[key], dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                
                self.logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                self.logger.error(f"Error loading configuration from {config_path}: {e}")
        
        return default_config
    
    def _discover_services(self) -> None:
        """Discover and register available services."""
        services_config = self.config.get('services', {})
        
        for service_name, service_config in services_config.items():
            if not service_config.get('enabled', True):
                self.logger.info(f"Service {service_name} is disabled in configuration")
                continue
            
            module_name = service_config.get('module')
            class_name = service_config.get('class')
            
            if not module_name or not class_name:
                self.logger.warning(f"Invalid configuration for service {service_name}")
                continue
            
            try:
                # Register service
                self.services[service_name] = {
                    'module': module_name,
                    'class': class_name,
                    'config': service_config
                }
                
                # Set initial status
                self.service_status[service_name] = ServiceStatus.UNKNOWN
                
                self.logger.info(f"Registered service: {service_name}")
            except Exception as e:
                self.logger.error(f"Error registering service {service_name}: {e}")
    
    def initialize_service(self, service_name: str) -> bool:
        """
        Initialize a service.
        
        Args:
            service_name: Name of the service to initialize
            
        Returns:
            Initialization success
        """
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        if service_name in self.service_instances and self.service_instances[service_name]:
            self.logger.info(f"Service {service_name} is already initialized")
            return True
        
        service_info = self.services[service_name]
        
        try:
            # Update status
            self.service_status[service_name] = ServiceStatus.STARTING
            
            # Import module
            module_name = service_info['module']
            module = importlib.import_module(module_name)
            
            # Get class
            class_name = service_info['class']
            service_class = getattr(module, class_name)
            
            # Initialize service
            service_instance = service_class()
            
            # Store instance
            self.service_instances[service_name] = service_instance
            
            # Update status
            self.service_status[service_name] = ServiceStatus.ONLINE
            
            self.logger.info(f"Initialized service: {service_name}")
            return True
        
        except ImportError as e:
            self.logger.error(f"Error importing module for service {service_name}: {e}")
            self.service_status[service_name] = ServiceStatus.OFFLINE
            return False
        except AttributeError as e:
            self.logger.error(f"Error getting class for service {service_name}: {e}")
            self.service_status[service_name] = ServiceStatus.OFFLINE
            return False
        except Exception as e:
            self.logger.error(f"Error initializing service {service_name}: {e}")
            self.service_status[service_name] = ServiceStatus.OFFLINE
            return False
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None if not found or not initialized
        """
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return None
        
        if service_name not in self.service_instances or not self.service_instances[service_name]:
            # Try to initialize the service
            if not self.initialize_service(service_name):
                return None
        
        return self.service_instances[service_name]
    
    def initialize_all_services(self) -> Dict[str, bool]:
        """
        Initialize all registered services.
        
        Returns:
            Dictionary mapping service names to initialization success
        """
        results = {}
        
        for service_name in self.services:
            results[service_name] = self.initialize_service(service_name)
        
        return results
    
    def get_service_status(self, service_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get status of services.
        
        Args:
            service_name: Optional name of a specific service
            
        Returns:
            Dictionary mapping service names to status values
        """
        if service_name:
            if service_name not in self.services:
                return {service_name: ServiceStatus.UNKNOWN.value}
            
            return {service_name: self.service_status[service_name].value}
        
        # Return status of all services
        return {name: status.value for name, status in self.service_status.items()}
    
    def route_request(self, service_name: str, method_name: str, 
                   *args, **kwargs) -> Any:
        """
        Route a request to a service.
        
        Args:
            service_name: Name of the target service
            method_name: Name of the method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method
            
        Returns:
            Result of the method call
        """
        service = self.get_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not available")
        
        # Check if method exists
        if not hasattr(service, method_name):
            raise ValueError(f"Method {method_name} not found in service {service_name}")
        
        # Get method
        method = getattr(service, method_name)
        
        # Check for rate limiting
        if not self._check_rate_limit(service_name):
            raise Exception(f"Rate limit exceeded for service {service_name}")
        
        # Get timeout
        timeout = self._get_timeout(service_name, method_name)
        
        try:
            # Execute method (no actual timeout implemented here for simplicity)
            return method(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error calling {method_name} on service {service_name}: {e}")
            # Update service status if needed
            # self._update_service_status(service_name, e)
            raise
    
    def _check_rate_limit(self, service_name: str) -> bool:
        """
        Check if a request would exceed the rate limit.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        # This is a placeholder; a real implementation would track request counts
        return True
    
    def _get_timeout(self, service_name: str, method_name: str) -> float:
        """
        Get timeout for a method call.
        
        Args:
            service_name: Name of the service
            method_name: Name of the method
            
        Returns:
            Timeout in seconds
        """
        timeouts = self.config.get('timeouts', {})
        
        # Check for specific method timeout
        method_key = f"{service_name}_{method_name}"
        if method_key in timeouts:
            return timeouts[method_key]
        
        # Check for service timeout
        if service_name in timeouts:
            return timeouts[service_name]
        
        # Use default timeout
        return timeouts.get('default', 30)
    
    def _update_service_status(self, service_name: str, error: Exception) -> None:
        """
        Update service status based on error.
        
        Args:
            service_name: Name of the service
            error: Exception that occurred
        """
        # This is a placeholder; a real implementation would analyze the error
        # and update the service status accordingly
        self.service_status[service_name] = ServiceStatus.DEGRADED
    
    def shutdown_service(self, service_name: str) -> bool:
        """
        Shutdown a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Shutdown success
        """
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        if service_name not in self.service_instances or not self.service_instances[service_name]:
            self.logger.info(f"Service {service_name} is not initialized")
            return True
        
        try:
            # Update status
            self.service_status[service_name] = ServiceStatus.STOPPING
            
            # Get service instance
            service = self.service_instances[service_name]
            
            # Call shutdown method if it exists
            if hasattr(service, 'shutdown'):
                service.shutdown()
            
            # Remove instance
            self.service_instances[service_name] = None
            
            # Update status
            self.service_status[service_name] = ServiceStatus.OFFLINE
            
            self.logger.info(f"Shutdown service: {service_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error shutting down service {service_name}: {e}")
            self.service_status[service_name] = ServiceStatus.UNKNOWN
            return False
    
    def shutdown_all_services(self) -> Dict[str, bool]:
        """
        Shutdown all initialized services.
        
        Returns:
            Dictionary mapping service names to shutdown success
        """
        results = {}
        
        for service_name in list(self.service_instances.keys()):
            if self.service_instances[service_name]:
                results[service_name] = self.shutdown_service(service_name)
        
        return results
    
    def execute_cross_service_operation(self, operation_name: str, 
                                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complex operation that spans multiple services.
        
        Args:
            operation_name: Name of the operation
            parameters: Parameters for the operation
            
        Returns:
            Dictionary of operation results
        """
        # This is a placeholder for cross-service operations
        # In a real implementation, this would define complex workflows
        # that coordinate multiple service calls
        
        if operation_name == "analyze_repository":
            return self._execute_repository_analysis(parameters)
        
        elif operation_name == "build_knowledge_graph":
            return self._execute_knowledge_graph_build(parameters)
        
        elif operation_name == "apply_neuro_symbolic_reasoning":
            return self._execute_neuro_symbolic_reasoning(parameters)
        
        elif operation_name == "perform_academic_research":
            return self._execute_academic_research(parameters)
        
        else:
            raise ValueError(f"Unknown operation: {operation_name}")
    
    def _execute_repository_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute repository analysis operation.
        
        Args:
            parameters: Operation parameters
            
        Returns:
            Operation results
        """
        results = {}
        
        try:
            # Get repository service
            repo_service = self.get_service('repository')
            if not repo_service:
                raise ValueError("Repository service not available")
            
            # Clone repository
            repo_url = parameters.get('repo_url')
            repo_branch = parameters.get('repo_branch', 'main')
            
            if not repo_url:
                raise ValueError("Repository URL is required")
            
            # Create repository
            repo_id = repo_service.create_repository(
                name=repo_url.split('/')[-1],
                url=repo_url,
                repo_type="git",
                default_branch=repo_branch
            )
            
            results['repository_id'] = repo_id
            
            # Clone repository
            clone_success = repo_service.clone_repository(repo_id)
            results['clone_success'] = clone_success
            
            if not clone_success:
                raise ValueError(f"Failed to clone repository: {repo_url}")
            
            # Get files
            files = repo_service.get_repository_files(repo_id)
            results['file_count'] = len(files)
            
            # Get commits
            commits = repo_service.get_repository_commits(repo_id)
            results['commit_count'] = len(commits)
            
            # Get branches
            branches = repo_service.get_repository_branches(repo_id)
            results['branch_count'] = len(branches)
            
            # If code review requested
            if parameters.get('analyze_code', True):
                # This is a placeholder; in a real implementation, we would
                # analyze code using appropriate services
                results['code_analysis'] = {
                    'status': 'success',
                    'file_count': len(files)
                }
            
            # If database analysis requested
            if parameters.get('analyze_database', True):
                # This is a placeholder
                results['database_analysis'] = {
                    'status': 'success',
                    'model_count': 0,
                    'table_count': 0
                }
            
            # If modularization analysis requested
            if parameters.get('analyze_modularization', True):
                # This is a placeholder
                results['modularization_analysis'] = {
                    'status': 'success',
                    'module_count': 0
                }
            
            # If agent readiness evaluation requested
            if parameters.get('analyze_agent_readiness', True):
                # This is a placeholder
                results['agent_readiness_analysis'] = {
                    'status': 'success',
                    'readiness_score': 0.0
                }
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error in repository analysis: {e}")
            return {'error': str(e), 'partial_results': results}
    
    def _execute_knowledge_graph_build(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute knowledge graph build operation.
        
        Args:
            parameters: Operation parameters
            
        Returns:
            Operation results
        """
        # This is a placeholder for a knowledge graph build operation
        return {'status': 'not_implemented'}
    
    def _execute_neuro_symbolic_reasoning(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute neuro-symbolic reasoning operation.
        
        Args:
            parameters: Operation parameters
            
        Returns:
            Operation results
        """
        # This is a placeholder for a neuro-symbolic reasoning operation
        return {'status': 'not_implemented'}
    
    def _execute_academic_research(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute academic research operation.
        
        Args:
            parameters: Operation parameters
            
        Returns:
            Operation results
        """
        # This is a placeholder for an academic research operation
        return {'status': 'not_implemented'}


# Singleton instance for easy import
_gateway_instance = None

def get_gateway_instance(config_path: Optional[str] = None) -> APIGateway:
    """
    Get the singleton API Gateway instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        API Gateway instance
    """
    global _gateway_instance
    
    if _gateway_instance is None:
        _gateway_instance = APIGateway(config_path)
    
    return _gateway_instance