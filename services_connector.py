"""
Services Connector

This module provides a central connector for all microservices in the system.
It handles service discovery, initialization, and communication.
"""

import os
import logging
import importlib
import time
from typing import Dict, List, Any, Optional, Union, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServicesConnector:
    """
    Central connector for all microservices in the system.
    
    This class provides:
    - Service discovery and initialization
    - Service status monitoring
    - Unified API for interacting with all services
    """
    
    def __init__(self, services_dir: str = 'services'):
        """
        Initialize the services connector.
        
        Args:
            services_dir: Directory containing service packages
        """
        self.services_dir = services_dir
        self.services = {}  # service_name -> service_instance
        self.service_status = {}  # service_name -> status
        
        # Discover available services
        self._discover_services()
    
    def _discover_services(self) -> None:
        """Discover available services in the services directory."""
        if not os.path.exists(self.services_dir):
            logger.warning(f"Services directory '{self.services_dir}' not found")
            return
        
        # Get all directories in services_dir (each directory is a service)
        service_packages = [
            d for d in os.listdir(self.services_dir)
            if os.path.isdir(os.path.join(self.services_dir, d)) and not d.startswith('__')
        ]
        
        logger.info(f"Discovered service packages: {service_packages}")
        
        # Initialize service status
        for service_name in service_packages:
            self.service_status[service_name] = 'discovered'
    
    def initialize_service(self, service_name: str) -> Optional[Any]:
        """
        Initialize a specific service.
        
        Args:
            service_name: Name of the service to initialize
            
        Returns:
            Service instance or None if initialization failed
        """
        if service_name not in self.service_status:
            logger.warning(f"Service '{service_name}' not found")
            return None
        
        if service_name in self.services:
            logger.info(f"Service '{service_name}' already initialized")
            return self.services[service_name]
        
        try:
            # Update service status
            self.service_status[service_name] = 'initializing'
            
            # Import service module
            module_path = f"{self.services_dir}.{service_name}"
            
            try:
                service_module = importlib.import_module(module_path)
                logger.info(f"Imported service module: {module_path}")
            except ImportError as e:
                logger.error(f"Error importing service module '{module_path}': {e}")
                self.service_status[service_name] = 'failed'
                return None
            
            # Initialize service based on the service type
            service_instance = None
            
            # Knowledge Graph service
            if service_name == 'knowledge_graph':
                try:
                    from services.knowledge_graph.knowledge_graph import KnowledgeGraph
                    service_instance = KnowledgeGraph()
                    logger.info("Initialized Knowledge Graph service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing Knowledge Graph service: {e}")
            
            # Academic service
            elif service_name == 'academic':
                try:
                    from services.academic.academic_framework import AcademicFramework
                    service_instance = AcademicFramework()
                    logger.info("Initialized Academic Framework service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing Academic Framework service: {e}")
            
            # Neuro-Symbolic service
            elif service_name == 'neuro_symbolic':
                try:
                    from services.neuro_symbolic.reasoning_engine import ReasoningEngine
                    service_instance = ReasoningEngine()
                    logger.info("Initialized Neuro-Symbolic Reasoning Engine service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing Neuro-Symbolic Reasoning Engine service: {e}")
            
            # Multimodal service
            elif service_name == 'multimodal':
                try:
                    from services.multimodal.multimodal_processor import MultimodalProcessor
                    service_instance = MultimodalProcessor()
                    logger.info("Initialized Multimodal Processor service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing Multimodal Processor service: {e}")
            
            # Model Hub service
            elif service_name == 'model_hub':
                try:
                    from services.model_hub.model_registry import ModelRegistry
                    service_instance = ModelRegistry()
                    logger.info("Initialized Model Registry service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing Model Registry service: {e}")
            
            # Agent Orchestrator service
            elif service_name == 'agent_orchestrator':
                try:
                    from services.agent_orchestrator.orchestrator import AgentOrchestrator
                    service_instance = AgentOrchestrator()
                    logger.info("Initialized Agent Orchestrator service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing Agent Orchestrator service: {e}")
            
            # API Gateway service
            elif service_name == 'api_gateway':
                try:
                    from services.api_gateway.gateway import APIGateway
                    service_instance = APIGateway()
                    logger.info("Initialized API Gateway service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing API Gateway service: {e}")
            
            # SDK service
            elif service_name == 'sdk':
                try:
                    from services.sdk.plugin_system import PluginSystem
                    service_instance = PluginSystem()
                    logger.info("Initialized SDK Plugin System service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing SDK Plugin System service: {e}")
                    
            # AI Models service
            elif service_name == 'ai_models':
                try:
                    from services.ai_models.ai_service import AIService
                    service_instance = AIService()
                    logger.info("Initialized AI Models service")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error initializing AI Models service: {e}")
            
            # Generic fallback for other services
            else:
                try:
                    # Try to find a main class in the service package
                    main_module_path = f"{module_path}.{service_name}"
                    try:
                        main_module = importlib.import_module(main_module_path)
                        
                        # Look for a class with the service name
                        service_class_name = ''.join(word.capitalize() for word in service_name.split('_'))
                        if hasattr(main_module, service_class_name):
                            service_class = getattr(main_module, service_class_name)
                            service_instance = service_class()
                            logger.info(f"Initialized generic service: {service_name}")
                        else:
                            logger.warning(f"No service class found for {service_name}")
                            self.service_status[service_name] = 'unavailable'
                    
                    except (ImportError, AttributeError) as e:
                        logger.warning(f"Error initializing generic service '{service_name}': {e}")
                        self.service_status[service_name] = 'unavailable'
                
                except Exception as e:
                    logger.error(f"Unexpected error initializing service '{service_name}': {e}")
                    self.service_status[service_name] = 'failed'
            
            # Store service instance if initialization succeeded
            if service_instance is not None:
                self.services[service_name] = service_instance
                self.service_status[service_name] = 'active'
                return service_instance
            else:
                self.service_status[service_name] = 'failed'
                return None
        
        except Exception as e:
            logger.error(f"Error initializing service '{service_name}': {e}")
            self.service_status[service_name] = 'failed'
            return None
    
    def initialize_all_services(self) -> Dict[str, Any]:
        """
        Initialize all available services.
        
        Returns:
            Dictionary of initialized services (service_name -> service_instance)
        """
        initialized_services = {}
        
        for service_name in list(self.service_status.keys()):
            service_instance = self.initialize_service(service_name)
            
            if service_instance is not None:
                initialized_services[service_name] = service_instance
        
        return initialized_services
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a service instance by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None if not found
        """
        if service_name in self.services:
            return self.services[service_name]
        
        # Try to initialize the service if not already initialized
        return self.initialize_service(service_name)
    
    def get_service_status(self) -> Dict[str, str]:
        """
        Get the status of all services.
        
        Returns:
            Dictionary of service statuses (service_name -> status)
        """
        return self.service_status.copy()

    def knowledge_graph_service(self) -> Any:
        """
        Get the Knowledge Graph service.
        
        Returns:
            Knowledge Graph service instance
        """
        return self.get_service('knowledge_graph')
    
    def academic_service(self) -> Any:
        """
        Get the Academic Framework service.
        
        Returns:
            Academic Framework service instance
        """
        return self.get_service('academic')
    
    def neuro_symbolic_service(self) -> Any:
        """
        Get the Neuro-Symbolic Reasoning Engine service.
        
        Returns:
            Neuro-Symbolic Reasoning Engine service instance
        """
        return self.get_service('neuro_symbolic')
    
    def multimodal_service(self) -> Any:
        """
        Get the Multimodal Processor service.
        
        Returns:
            Multimodal Processor service instance
        """
        return self.get_service('multimodal')
    
    def model_hub_service(self) -> Any:
        """
        Get the Model Registry service.
        
        Returns:
            Model Registry service instance
        """
        return self.get_service('model_hub')
    
    def agent_orchestrator_service(self) -> Any:
        """
        Get the Agent Orchestrator service.
        
        Returns:
            Agent Orchestrator service instance
        """
        return self.get_service('agent_orchestrator')
    
    def api_gateway_service(self) -> Any:
        """
        Get the API Gateway service.
        
        Returns:
            API Gateway service instance
        """
        return self.get_service('api_gateway')
    
    def sdk_service(self) -> Any:
        """
        Get the SDK Plugin System service.
        
        Returns:
            SDK Plugin System service instance
        """
        return self.get_service('sdk')
        
    def ai_models_service(self) -> Any:
        """
        Get the AI Models service.
        
        Returns:
            AI Models service instance
        """
        return self.get_service('ai_models')
    
    def analyze_repository(self, repo_url: str, repo_branch: str = 'main', 
                          use_services: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze a repository using available services.
        
        Args:
            repo_url: URL of the repository to analyze
            repo_branch: Branch of the repository to analyze
            use_services: Optional list of service names to use for analysis
            
        Returns:
            Dictionary of analysis results
        """
        results = {}
        
        # Default to all relevant services if not specified
        if use_services is None:
            use_services = [
                'knowledge_graph',
                'academic',
                'neuro_symbolic',
                'multimodal',
                'model_hub',
                'agent_orchestrator'
            ]
        
        # Clone repository (this would typically be done by a repository handler service)
        # For now, we'll just pass the repository URL to services that need it
        
        # Use each requested service for analysis
        for service_name in use_services:
            if service_name not in self.service_status:
                logger.warning(f"Service '{service_name}' not found")
                continue
            
            service = self.get_service(service_name)
            
            if service is None:
                logger.warning(f"Service '{service_name}' could not be initialized")
                continue
            
            try:
                # Here we'd call the appropriate analysis method for each service
                # For simplicity, we'll just add a placeholder result
                # In a real implementation, we'd call service-specific methods
                
                results[service_name] = {
                    'service': service_name,
                    'status': 'analysis_complete',
                    'findings': f"{service_name} analysis findings would go here",
                    'timestamp': time.time()
                }
                
                logger.info(f"Completed {service_name} analysis for {repo_url}")
            
            except Exception as e:
                logger.error(f"Error in {service_name} analysis: {e}")
                results[service_name] = {
                    'service': service_name,
                    'status': 'analysis_failed',
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        return results
    
    def shutdown(self) -> None:
        """Shut down all services gracefully."""
        for service_name, service in list(self.services.items()):
            try:
                # Call shutdown method if it exists
                if hasattr(service, 'shutdown') and callable(getattr(service, 'shutdown')):
                    service.shutdown()
                
                logger.info(f"Shut down service: {service_name}")
            
            except Exception as e:
                logger.error(f"Error shutting down service '{service_name}': {e}")
            
            # Remove from services dict
            self.services.pop(service_name, None)
            
            # Update status
            self.service_status[service_name] = 'shutdown'