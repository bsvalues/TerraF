"""
API Gateway Implementation

This module implements the core functionality of the API Gateway service.
"""
import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
import uuid

class APIGateway:
    """
    API Gateway for the Code Deep Dive Analyzer microservices.
    
    This class provides:
    - Request routing to appropriate microservices
    - Authentication and authorization
    - Rate limiting
    - Request/response transformation
    - Service discovery
    - Logging and monitoring
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the API Gateway with optional configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.services = {}
        self.routes = {}
        self.auth_providers = {}
        self.rate_limits = {}
        self.logger = logging.getLogger('api_gateway')
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self._init_service_registry()
        self._init_auth_providers()
        self._init_rate_limiters()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'service_registry': {
                'refresh_interval': 60,  # seconds
                'service_timeout': 5,    # seconds
            },
            'auth': {
                'token_expiry': 86400,   # 24 hours
                'refresh_token_expiry': 604800,  # 7 days
                'allowed_algorithms': ['HS256', 'RS256'],
            },
            'rate_limiting': {
                'default_limit': 100,    # requests per minute
                'burst_limit': 200,      # max burst
            },
            'cors': {
                'allowed_origins': ['*'],
                'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                'allowed_headers': ['Content-Type', 'Authorization'],
                'expose_headers': ['X-Total-Count'],
                'max_age': 86400,
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge configs
                    self._deep_merge(default_config, user_config)
            except Exception as e:
                self.logger.error(f"Failed to load config from {config_path}: {str(e)}")
                self.logger.info("Using default configuration")
        
        return default_config
    
    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """
        Deep merge two dictionaries.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _init_service_registry(self) -> None:
        """Initialize the service registry."""
        # In a real implementation, this would connect to a service registry like Consul or etcd
        # For this example, we'll use a simple in-memory registry
        self.service_registry = {
            'model_hub': {
                'instances': [
                    {'host': 'localhost', 'port': 5001, 'health': 'healthy', 'last_checked': time.time()}
                ],
                'api_version': 'v1',
            },
            'code_analyzer': {
                'instances': [
                    {'host': 'localhost', 'port': 5002, 'health': 'healthy', 'last_checked': time.time()}
                ],
                'api_version': 'v1',
            },
            'repository_service': {
                'instances': [
                    {'host': 'localhost', 'port': 5003, 'health': 'healthy', 'last_checked': time.time()}
                ],
                'api_version': 'v1',
            },
            'agent_orchestrator': {
                'instances': [
                    {'host': 'localhost', 'port': 5004, 'health': 'healthy', 'last_checked': time.time()}
                ],
                'api_version': 'v1',
            },
            'continuous_learning': {
                'instances': [
                    {'host': 'localhost', 'port': 5005, 'health': 'healthy', 'last_checked': time.time()}
                ],
                'api_version': 'v1',
            },
            'visualization_service': {
                'instances': [
                    {'host': 'localhost', 'port': 5006, 'health': 'healthy', 'last_checked': time.time()}
                ],
                'api_version': 'v1',
            },
        }
    
    def _init_auth_providers(self) -> None:
        """Initialize authentication providers."""
        # In a real implementation, this would initialize various auth providers
        # For this example, we'll use a placeholder
        self.auth_providers = {
            'jwt': lambda token: {'user_id': 'user123', 'roles': ['user']},
            'api_key': lambda key: {'client_id': 'client123', 'scopes': ['read', 'write']},
        }
    
    def _init_rate_limiters(self) -> None:
        """Initialize rate limiters."""
        # In a real implementation, this would initialize rate limiters with Redis or similar
        # For this example, we'll use a simple in-memory counter
        self.rate_limiters = {
            'default': {
                'limit': self.config['rate_limiting']['default_limit'],
                'window': 60,  # seconds
                'counters': {}
            }
        }
    
    def route_request(self, service_name: str, path: str, method: str, 
                      headers: Dict[str, str], body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route a request to the appropriate microservice.
        
        Args:
            service_name: Name of the target service
            path: API endpoint path
            method: HTTP method (GET, POST, etc.)
            headers: HTTP headers
            body: Request body (for POST, PUT, etc.)
            
        Returns:
            Response from the service
        """
        # Check if service exists
        if service_name not in self.service_registry:
            return {
                'status_code': 404,
                'body': {'error': f"Service '{service_name}' not found"}
            }
        
        # Authenticate request
        auth_result = self._authenticate_request(headers)
        if not auth_result['authenticated']:
            return {
                'status_code': 401,
                'body': {'error': auth_result['error']}
            }
        
        # Check rate limits
        rate_limit_result = self._check_rate_limits(auth_result['identity'])
        if not rate_limit_result['allowed']:
            return {
                'status_code': 429,
                'body': {'error': 'Rate limit exceeded', 'retry_after': rate_limit_result['retry_after']}
            }
        
        # Get service instance
        service = self._get_service_instance(service_name)
        if not service:
            return {
                'status_code': 503,
                'body': {'error': f"No healthy instances of service '{service_name}' available"}
            }
        
        # In a real implementation, this would make an actual HTTP request to the service
        # For this example, we'll simulate a response
        return self._simulate_service_response(service_name, path, method, auth_result['identity'], body)
    
    def _authenticate_request(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Authenticate a request based on headers.
        
        Args:
            headers: HTTP headers
            
        Returns:
            Authentication result
        """
        # Check for Authorization header
        auth_header = headers.get('Authorization')
        if not auth_header:
            return {'authenticated': False, 'error': 'Authorization header is missing'}
        
        # Parse auth method and token
        parts = auth_header.split()
        if len(parts) != 2:
            return {'authenticated': False, 'error': 'Invalid Authorization header format'}
        
        auth_method, token = parts
        
        # Handle different auth methods
        if auth_method.lower() == 'bearer':
            # JWT authentication
            if 'jwt' in self.auth_providers:
                try:
                    identity = self.auth_providers['jwt'](token)
                    return {'authenticated': True, 'identity': identity}
                except Exception as e:
                    return {'authenticated': False, 'error': f"JWT validation failed: {str(e)}"}
        elif auth_method.lower() == 'apikey':
            # API key authentication
            if 'api_key' in self.auth_providers:
                try:
                    identity = self.auth_providers['api_key'](token)
                    return {'authenticated': True, 'identity': identity}
                except Exception as e:
                    return {'authenticated': False, 'error': f"API key validation failed: {str(e)}"}
        
        return {'authenticated': False, 'error': f"Unsupported authentication method: {auth_method}"}
    
    def _check_rate_limits(self, identity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a request exceeds rate limits.
        
        Args:
            identity: Authenticated identity
            
        Returns:
            Rate limit check result
        """
        # In a real implementation, this would check against a distributed rate limiter
        # For this example, we'll always allow requests
        return {'allowed': True}
    
    def _get_service_instance(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a healthy instance of a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None if no healthy instances available
        """
        if service_name not in self.service_registry:
            return None
        
        # Get all healthy instances
        healthy_instances = [
            instance for instance in self.service_registry[service_name]['instances']
            if instance['health'] == 'healthy'
        ]
        
        if not healthy_instances:
            return None
        
        # In a real implementation, this would use a load balancing algorithm
        # For this example, we'll just return the first healthy instance
        return healthy_instances[0]
    
    def _simulate_service_response(self, service_name: str, path: str, method: str, 
                                  identity: Dict[str, Any], body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simulate a response from a microservice.
        
        Args:
            service_name: Name of the service
            path: API endpoint path
            method: HTTP method
            identity: Authenticated identity
            body: Request body
            
        Returns:
            Simulated response
        """
        # This is just a placeholder for simulation
        # In a real implementation, this would make an actual HTTP request to the service
        
        # Generate a request ID for tracing
        request_id = str(uuid.uuid4())
        
        # Log the request
        self.logger.info(f"Request {request_id}: {method} {service_name}{path}")
        
        # Simulate some processing time
        time.sleep(0.1)
        
        # Return a simulated response
        return {
            'status_code': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': request_id
            },
            'body': {
                'service': service_name,
                'path': path,
                'method': method,
                'timestamp': time.time(),
                'request_id': request_id,
                'message': 'Request processed successfully'
            }
        }
    
    def register_service(self, service_name: str, host: str, port: int) -> bool:
        """
        Register a new service instance.
        
        Args:
            service_name: Name of the service
            host: Service host
            port: Service port
            
        Returns:
            Registration success
        """
        if service_name not in self.service_registry:
            self.service_registry[service_name] = {
                'instances': [],
                'api_version': 'v1'
            }
        
        # Check if instance already registered
        for instance in self.service_registry[service_name]['instances']:
            if instance['host'] == host and instance['port'] == port:
                # Update health and timestamp
                instance['health'] = 'healthy'
                instance['last_checked'] = time.time()
                return True
        
        # Add new instance
        self.service_registry[service_name]['instances'].append({
            'host': host,
            'port': port,
            'health': 'healthy',
            'last_checked': time.time()
        })
        
        self.logger.info(f"Registered new instance of service '{service_name}' at {host}:{port}")
        return True
    
    def deregister_service(self, service_name: str, host: str, port: int) -> bool:
        """
        Deregister a service instance.
        
        Args:
            service_name: Name of the service
            host: Service host
            port: Service port
            
        Returns:
            Deregistration success
        """
        if service_name not in self.service_registry:
            return False
        
        # Find and remove the instance
        instances = self.service_registry[service_name]['instances']
        for i, instance in enumerate(instances):
            if instance['host'] == host and instance['port'] == port:
                instances.pop(i)
                self.logger.info(f"Deregistered instance of service '{service_name}' at {host}:{port}")
                return True
        
        return False
    
    def update_service_health(self, service_name: str, host: str, port: int, health: str) -> bool:
        """
        Update the health status of a service instance.
        
        Args:
            service_name: Name of the service
            host: Service host
            port: Service port
            health: Health status ('healthy' or 'unhealthy')
            
        Returns:
            Update success
        """
        if service_name not in self.service_registry:
            return False
        
        # Find and update the instance
        for instance in self.service_registry[service_name]['instances']:
            if instance['host'] == host and instance['port'] == port:
                old_health = instance['health']
                instance['health'] = health
                instance['last_checked'] = time.time()
                
                if old_health != health:
                    self.logger.info(
                        f"Service '{service_name}' at {host}:{port} changed health from '{old_health}' to '{health}'"
                    )
                
                return True
        
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the API Gateway.
        
        Returns:
            Health check result
        """
        # In a real implementation, this would check resources like database connections
        
        service_counts = {}
        healthy_counts = {}
        
        for service_name, service_info in self.service_registry.items():
            service_counts[service_name] = len(service_info['instances'])
            healthy_counts[service_name] = sum(
                1 for instance in service_info['instances'] if instance['health'] == 'healthy'
            )
        
        return {
            'status': 'healthy',
            'timestamp': time.time(),
            'service_registry': {
                'total_services': len(self.service_registry),
                'service_counts': service_counts,
                'healthy_counts': healthy_counts
            }
        }