"""
TerraFusion Bridge Module

This module provides a bridge between the Streamlit Python application and the Node.js/TypeScript
microservices in the monorepo. It enables calling JavaScript/TypeScript functions from Python,
and vice versa, maintaining compatibility during the migration.

Usage example:
    from bridge import call_service, register_callback

    # Call a TypeScript service from Python
    result = call_service('marketplace', 'getPlugins', {'limit': 10})

    # Register a Python callback that can be called from TypeScript
    @register_callback('on_plugin_installed')
    def handle_plugin_installed(plugin_id, workspace_id):
        print(f"Plugin {plugin_id} was installed in workspace {workspace_id}")
"""

import json
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import logging

import requests
from queue import Queue
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_PORT = 4000  # Default port for the Express API server
SERVICE_BASE_URL = os.environ.get("API_BASE_URL", f"http://localhost:{SERVICE_PORT}")
REQUEST_TIMEOUT = 30  # seconds

# Store registered callbacks
_callbacks: Dict[str, Callable] = {}

# Queue for bridge events
_event_queue: Queue = Queue()

# Authentication token cache
_auth_token: Optional[str] = None


class BridgeException(Exception):
    """Exception raised for errors in the bridge."""
    
    def __init__(self, message: str, service: str = "", method: str = "", status_code: Optional[int] = None):
        self.message = message
        self.service = service
        self.method = method
        self.status_code = status_code
        super().__init__(f"Bridge error: {message}")


def _get_auth_token() -> Optional[str]:
    """Get the current authentication token from session or cache."""
    global _auth_token
    
    # First check session state
    if "auth_token" in st.session_state:
        return st.session_state.auth_token
    
    # Then check cache
    return _auth_token


def _set_auth_token(token: str) -> None:
    """Set the authentication token in both session and cache."""
    global _auth_token
    
    # Store in session state if available
    if "session_state" in globals():
        st.session_state.auth_token = token
    
    # Store in module cache
    _auth_token = token


def call_service(
    service: str, 
    method: str, 
    params: Optional[Dict[str, Any]] = None,
    auth_required: bool = True
) -> Any:
    """
    Call a service method in the TypeScript/Node.js backend.
    
    Args:
        service: The name of the service to call (e.g., 'marketplace', 'workflow')
        method: The method name to call within the service
        params: Optional parameters to pass to the method
        auth_required: Whether authentication is required for this call
        
    Returns:
        The result from the service method
        
    Raises:
        BridgeException: If an error occurs in the bridge communication
    """
    url = f"{SERVICE_BASE_URL}/api/{service}/{method}"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add authentication token if required
    if auth_required:
        token = _get_auth_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            logger.warning(f"Auth required for {service}.{method} but no token available")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=params or {},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()
        else:
            error_msg = f"Service call failed: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_msg = error_data["error"]["message"]
            except:
                error_msg = response.text or error_msg
                
            raise BridgeException(
                message=error_msg,
                service=service,
                method=method,
                status_code=response.status_code
            )
    
    except requests.RequestException as e:
        logger.error(f"Request error calling {service}.{method}: {str(e)}")
        raise BridgeException(
            message=f"Communication error: {str(e)}",
            service=service,
            method=method
        )


def register_callback(event_name: str) -> Callable[[Callable], Callable]:
    """
    Decorator to register a Python function as a callback for an event.
    
    Args:
        event_name: The name of the event to register for
        
    Returns:
        Decorator function that registers the callback
    """
    def decorator(func: Callable) -> Callable:
        _callbacks[event_name] = func
        logger.info(f"Registered callback for event: {event_name}")
        return func
    
    return decorator


def call_callback(event_name: str, *args, **kwargs) -> Any:
    """
    Call a registered callback by name.
    
    Args:
        event_name: The name of the event/callback to trigger
        *args: Positional arguments to pass to the callback
        **kwargs: Keyword arguments to pass to the callback
        
    Returns:
        The result of the callback function
        
    Raises:
        BridgeException: If the callback is not registered
    """
    if event_name in _callbacks:
        try:
            return _callbacks[event_name](*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in callback {event_name}: {str(e)}")
            raise BridgeException(f"Callback error: {str(e)}")
    else:
        raise BridgeException(f"No callback registered for event: {event_name}")


def login(email: str, password: str) -> Dict[str, Any]:
    """
    Log in to the backend services and get an authentication token.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User data including the authentication token
        
    Raises:
        BridgeException: If login fails
    """
    try:
        result = call_service("auth", "login", {
            "email": email,
            "password": password
        }, auth_required=False)
        
        if "token" in result:
            _set_auth_token(result["token"])
            
        return result
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise BridgeException(f"Login failed: {str(e)}")


def logout() -> None:
    """
    Log out and clear the authentication token.
    """
    global _auth_token
    
    try:
        # Call the logout API endpoint
        call_service("auth", "logout", {}, auth_required=True)
    except Exception as e:
        logger.warning(f"Error during logout API call: {str(e)}")
    
    # Clear the token regardless of API call success
    if "session_state" in globals():
        if "auth_token" in st.session_state:
            del st.session_state.auth_token
    
    _auth_token = None


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the currently logged-in user information.
    
    Returns:
        User data dict or None if not logged in
    """
    try:
        return call_service("users", "me")
    except BridgeException as e:
        if e.status_code == 401:
            # Not authenticated, return None
            return None
        # For other errors, re-raise
        raise


def is_authenticated() -> bool:
    """
    Check if the user is currently authenticated.
    
    Returns:
        True if authenticated, False otherwise
    """
    return get_current_user() is not None


def get_plugins(limit: int = 10, offset: int = 0, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Get plugins from the marketplace.
    
    Args:
        limit: Maximum number of plugins to return
        offset: Number of plugins to skip for pagination
        category: Optional category filter
        
    Returns:
        Dict containing plugins and pagination info
    """
    params = {
        "limit": limit,
        "offset": offset
    }
    
    if category:
        params["category"] = category
        
    return call_service("market", "plugins", params, auth_required=False)


def get_plugin_details(plugin_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific plugin.
    
    Args:
        plugin_id: ID of the plugin
        
    Returns:
        Plugin details
    """
    return call_service("market", "pluginDetails", {"id": plugin_id}, auth_required=False)


def install_plugin(plugin_id: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Install or purchase a plugin.
    
    Args:
        plugin_id: ID of the plugin to install
        workspace_id: Optional workspace ID to install the plugin to
        
    Returns:
        Installation result
    """
    params = {"pluginId": plugin_id}
    
    if workspace_id:
        params["workspaceId"] = workspace_id
        
    return call_service("market", "purchasePlugin", params)


def get_user_plugins() -> List[Dict[str, Any]]:
    """
    Get the plugins installed by the current user.
    
    Returns:
        List of installed plugins
    """
    return call_service("market", "userPlugins")


def get_workflows(limit: int = 10, offset: int = 0, status: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the workflows for the current user.
    
    Args:
        limit: Maximum number of workflows to return
        offset: Number of workflows to skip for pagination
        status: Optional status filter
        
    Returns:
        Dict containing workflows and pagination info
    """
    params = {
        "limit": limit,
        "offset": offset
    }
    
    if status:
        params["status"] = status
        
    return call_service("workflows", "list", params)


def get_workflow_details(workflow_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific workflow.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Workflow details
    """
    return call_service("workflows", "details", {"id": workflow_id})


def run_workflow(workflow_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run a workflow.
    
    Args:
        workflow_id: ID of the workflow to run
        parameters: Optional parameters for the workflow
        
    Returns:
        Workflow run information
    """
    return call_service("workflows", "run", {
        "id": workflow_id,
        "parameters": parameters or {}
    })


def get_workflow_run_status(run_id: str) -> Dict[str, Any]:
    """
    Get the status of a workflow run.
    
    Args:
        run_id: ID of the workflow run
        
    Returns:
        Workflow run status information
    """
    return call_service("workflows", "runStatus", {"runId": run_id})


# Initialize bridge when module is imported
def _initialize_bridge():
    logger.info("Initializing TerraFusion bridge...")
    
    # Check if server is running
    try:
        response = requests.get(f"{SERVICE_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            logger.info("Successfully connected to TerraFusion API server")
        else:
            logger.warning(f"API server responded with status {response.status_code}")
    except requests.RequestException:
        logger.warning("Could not connect to API server. Some features may be unavailable.")


# Run initialization
_initialize_bridge()