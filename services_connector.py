"""
Services Connector

This module provides connectivity to all microservices in the Code Deep Dive Analyzer platform
and serves as a unified interface for the application.
"""
import os
import logging
import importlib
from typing import Dict, List, Any, Optional, Union

class ServicesConnector:
    """
    Connector for all microservices in the Code Deep Dive Analyzer platform.
    
    This class serves as a facade for the microservices architecture, providing
    a simplified interface for the application to interact with all services.
    """
    
    def __init__(self):
        """Initialize the services connector."""
        # Set up logger
        self.logger = logging.getLogger('services_connector')
        
        # Initialize service modules
        self.services = {}
        self.initialized_services = set()
        
        # Load service modules
        self._load_service_modules()
    
    def _load_service_modules(self):
        """Load all service modules dynamically."""
        # Define service mapping
        service_modules = {
            'api_gateway': 'services.api_gateway.gateway',
            'repository': 'services.repository_service.repository_manager',
            'model_hub': 'services.model_hub.model_registry',
            'neuro_symbolic': 'services.neuro_symbolic.reasoning_engine',
            'multimodal': 'services.multimodal.multimodal_processor',
            'agent_orchestrator': 'services.agent_orchestrator.orchestrator',
            'sdk': 'services.sdk.plugin_system',
            'knowledge_graph': 'services.knowledge_graph.knowledge_graph',
            'academic': 'services.academic.academic_framework'
        }
        
        # Load each service module
        for service_name, module_path in service_modules.items():
            try:
                # Check if directory exists
                module_parts = module_path.split('.')
                if len(module_parts) > 1:
                    service_dir = os.path.join(*module_parts[:-1])
                    if not os.path.exists(os.path.join(*service_dir.split('.'))):
                        self.logger.warning(f"Service directory not found for {service_name}, skipping")
                        continue
                
                # Import the module
                module = importlib.import_module(module_path)
                
                # Store the module
                self.services[service_name] = module
                
                self.logger.info(f"Loaded service module: {service_name}")
            
            except ImportError as e:
                self.logger.warning(f"Failed to import service module {service_name}: {e}")
            
            except Exception as e:
                self.logger.error(f"Error loading service module {service_name}: {e}")
    
    def initialize_service(self, service_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize a service.
        
        Args:
            service_name: Name of the service to initialize
            config: Optional configuration for the service
            
        Returns:
            Initialization success
        """
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not found")
            return False
        
        if service_name in self.initialized_services:
            self.logger.warning(f"Service {service_name} already initialized")
            return True
        
        try:
            module = self.services[service_name]
            
            # Initialize the service
            if service_name == 'api_gateway':
                self.api_gateway = module.ApiGateway(config=config)
                self.api_gateway.start()
            
            elif service_name == 'repository':
                self.repository_manager = module.RepositoryManager()
            
            elif service_name == 'model_hub':
                self.model_registry = module.ModelRegistry()
            
            elif service_name == 'neuro_symbolic':
                self.reasoning_engine = module.NeuroSymbolicEngine()
            
            elif service_name == 'multimodal':
                self.multimodal_processor = module.MultimodalProcessor()
            
            elif service_name == 'agent_orchestrator':
                self.agent_orchestrator = module.AgentOrchestrator()
                self.agent_orchestrator.start()
            
            elif service_name == 'sdk':
                self.plugin_manager = module.PluginManager()
            
            elif service_name == 'knowledge_graph':
                self.knowledge_graph = module.KnowledgeGraph()
            
            elif service_name == 'academic':
                self.academic_framework = module.AcademicFramework()
            
            # Mark as initialized
            self.initialized_services.add(service_name)
            
            self.logger.info(f"Initialized service: {service_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing service {service_name}: {e}")
            return False
    
    def initialize_all_services(self, configs: Optional[Dict[str, Dict[str, Any]]] = None) -> List[str]:
        """
        Initialize all available services.
        
        Args:
            configs: Optional dictionary mapping service names to configurations
            
        Returns:
            List of successfully initialized service names
        """
        configs = configs or {}
        initialized = []
        
        for service_name in self.services:
            config = configs.get(service_name)
            success = self.initialize_service(service_name, config)
            
            if success:
                initialized.append(service_name)
        
        return initialized
    
    def shutdown_service(self, service_name: str) -> bool:
        """
        Shutdown a service.
        
        Args:
            service_name: Name of the service to shutdown
            
        Returns:
            Shutdown success
        """
        if service_name not in self.initialized_services:
            self.logger.warning(f"Service {service_name} not initialized")
            return False
        
        try:
            # Shutdown the service
            if service_name == 'api_gateway':
                self.api_gateway.stop()
            
            elif service_name == 'agent_orchestrator':
                self.agent_orchestrator.stop()
            
            # Remove from initialized services
            self.initialized_services.remove(service_name)
            
            self.logger.info(f"Shutdown service: {service_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error shutting down service {service_name}: {e}")
            return False
    
    def shutdown_all_services(self) -> List[str]:
        """
        Shutdown all initialized services.
        
        Returns:
            List of successfully shutdown service names
        """
        shutdown = []
        
        for service_name in list(self.initialized_services):
            success = self.shutdown_service(service_name)
            
            if success:
                shutdown.append(service_name)
        
        return shutdown
    
    def register_services_with_gateway(self) -> bool:
        """
        Register all initialized services with the API Gateway.
        
        Returns:
            Registration success
        """
        if 'api_gateway' not in self.initialized_services:
            self.logger.error("API Gateway not initialized")
            return False
        
        try:
            # Register each service
            for service_name in self.initialized_services:
                if service_name == 'api_gateway':
                    continue
                
                # Define service information
                if service_name == 'repository':
                    self.api_gateway.register_service(
                        service_type='repository',
                        name='Repository Service',
                        base_url='http://localhost:5001',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/repositories',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/repositories/{id}',
                                'methods': ['GET', 'PUT', 'DELETE'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/repositories/{id}/analyze',
                                'methods': ['POST'],
                                'auth_level': 'user'
                            }
                        ],
                        health_endpoint='/health'
                    )
                
                elif service_name == 'model_hub':
                    self.api_gateway.register_service(
                        service_type='model_hub',
                        name='Model Hub',
                        base_url='http://localhost:5002',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/models',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/models/{id}',
                                'methods': ['GET', 'DELETE'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/models/{id}/versions',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            }
                        ],
                        health_endpoint='/health'
                    )
                
                elif service_name == 'neuro_symbolic':
                    self.api_gateway.register_service(
                        service_type='neuro_symbolic',
                        name='Neuro-Symbolic Engine',
                        base_url='http://localhost:5003',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/knowledge-bases',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/inference',
                                'methods': ['POST'],
                                'auth_level': 'user'
                            }
                        ],
                        health_endpoint='/health'
                    )
                
                elif service_name == 'multimodal':
                    self.api_gateway.register_service(
                        service_type='multimodal',
                        name='Multimodal Processor',
                        base_url='http://localhost:5004',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/content',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/content/{id}',
                                'methods': ['GET', 'PUT', 'DELETE'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/content/{id}/convert',
                                'methods': ['POST'],
                                'auth_level': 'user'
                            }
                        ],
                        health_endpoint='/health'
                    )
                
                elif service_name == 'agent_orchestrator':
                    self.api_gateway.register_service(
                        service_type='agent_orchestrator',
                        name='Agent Orchestrator',
                        base_url='http://localhost:5005',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/agents',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'admin'
                            },
                            {
                                'path': '/agents/{id}',
                                'methods': ['GET', 'PUT', 'DELETE'],
                                'auth_level': 'admin'
                            },
                            {
                                'path': '/tasks',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            }
                        ],
                        health_endpoint='/health'
                    )
                
                elif service_name == 'sdk':
                    self.api_gateway.register_service(
                        service_type='sdk',
                        name='SDK Plugin System',
                        base_url='http://localhost:5006',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/plugins',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'admin'
                            },
                            {
                                'path': '/plugins/{id}',
                                'methods': ['GET', 'PUT', 'DELETE'],
                                'auth_level': 'admin'
                            }
                        ],
                        health_endpoint='/health'
                    )
                
                elif service_name == 'knowledge_graph':
                    self.api_gateway.register_service(
                        service_type='knowledge_graph',
                        name='Knowledge Graph',
                        base_url='http://localhost:5007',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/graph',
                                'methods': ['GET'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/graph/nodes',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/graph/edges',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            }
                        ],
                        health_endpoint='/health'
                    )
                
                elif service_name == 'academic':
                    self.api_gateway.register_service(
                        service_type='academic',
                        name='Academic Framework',
                        base_url='http://localhost:5008',
                        version='1.0.0',
                        endpoints=[
                            {
                                'path': '/papers',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            },
                            {
                                'path': '/citations',
                                'methods': ['GET', 'POST'],
                                'auth_level': 'user'
                            }
                        ],
                        health_endpoint='/health'
                    )
            
            self.logger.info("Registered services with API Gateway")
            return True
        
        except Exception as e:
            self.logger.error(f"Error registering services with API Gateway: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, str]:
        """
        Get the status of all services.
        
        Returns:
            Dictionary mapping service names to status strings
        """
        status = {}
        
        for service_name in self.services:
            if service_name in self.initialized_services:
                status[service_name] = 'INITIALIZED'
            else:
                status[service_name] = 'NOT INITIALIZED'
        
        return status
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None if not found or not initialized
        """
        if service_name not in self.initialized_services:
            return None
        
        if service_name == 'api_gateway':
            return self.api_gateway
        elif service_name == 'repository':
            return self.repository_manager
        elif service_name == 'model_hub':
            return self.model_registry
        elif service_name == 'neuro_symbolic':
            return self.reasoning_engine
        elif service_name == 'multimodal':
            return self.multimodal_processor
        elif service_name == 'agent_orchestrator':
            return self.agent_orchestrator
        elif service_name == 'sdk':
            return self.plugin_manager
        elif service_name == 'knowledge_graph':
            return self.knowledge_graph
        elif service_name == 'academic':
            return self.academic_framework
        
        return None