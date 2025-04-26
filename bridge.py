"""
Bridge Module for Streamlit to New API Integration

This module provides a bridge for communication between the Streamlit application
and the new API services being developed as part of the migration to a modern
monorepo architecture.

It allows the existing Streamlit code to gradually adopt the new services
without requiring a complete rewrite all at once.
"""

import os
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
import requests
from requests.exceptions import RequestException

# Configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:4000')
API_VERSION = os.environ.get('API_VERSION', 'v1')
API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))

# Simple in-memory cache
_cache: Dict[str, Dict[str, Any]] = {}

def _generate_cache_key(endpoint: str, params: Dict[str, Any], cache_key: Optional[str] = None) -> str:
    """Generate a cache key for the API request."""
    params_str = json.dumps(params, sort_keys=True)
    key_parts = [endpoint, params_str]
    
    if cache_key:
        key_parts.append(cache_key)
    
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def call_api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
    cache_key: Optional[str] = None,
    cache_ttl: int = 60  # default 60 seconds
) -> Any:
    """
    Call the new API service from Streamlit.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        data: Request body data
        params: Query parameters
        headers: Request headers
        version: API version to use
        cache_key: Optional key for caching responses
        cache_ttl: Cache time-to-live in seconds
        
    Returns:
        API response data
        
    Raises:
        Exception: When API request fails
    """
    if params is None:
        params = {}
    
    if headers is None:
        headers = {}
    
    if version is None:
        version = API_VERSION
    
    url = f"{API_BASE_URL}/api/{version}/{endpoint.lstrip('/')}"
    
    # Handle caching for GET requests
    if method.upper() == "GET" and cache_key:
        cache_key_hash = _generate_cache_key(endpoint, params or {}, cache_key)
        
        # Check if we have a valid cached response
        if cache_key_hash in _cache:
            cache_entry = _cache[cache_key_hash]
            if (time.time() - cache_entry['timestamp']) < cache_ttl:
                print(f"[Bridge] Using cached data for {endpoint}")
                return cache_entry['data']
    
    # Set up headers
    request_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    request_headers.update(headers)
    
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            params=params,
            json=data,
            headers=request_headers,
            timeout=API_TIMEOUT
        )
        
        # Raise for HTTP errors
        response.raise_for_status()
        
        # Parse the response
        response_data = response.json()
        
        # Cache the response if appropriate
        if method.upper() == "GET" and cache_key:
            cache_key_hash = _generate_cache_key(endpoint, params or {}, cache_key)
            _cache[cache_key_hash] = {
                'data': response_data,
                'timestamp': time.time()
            }
        
        return response_data
    except RequestException as e:
        error_msg = f"API request failed: {e}"
        print(f"[Bridge] Error: {error_msg}")
        
        # Enhance the error with more details
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('message', '')}"
            except (ValueError, KeyError):
                pass
        
        raise Exception(error_msg) from e

def clear_cache() -> None:
    """Clear the API response cache."""
    global _cache
    _cache = {}
    print("[Bridge] Cache cleared")

# Domain-specific API methods
class MarketplaceAPI:
    """Marketplace API wrapper"""
    
    @staticmethod
    def list_plugins(params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List available plugins in the marketplace."""
        return call_api(
            endpoint="market/plugins",
            params=params or {},
            cache_key="plugins_list"
        )
    
    @staticmethod
    def get_plugin(plugin_id: str) -> Dict[str, Any]:
        """Get details for a specific plugin."""
        return call_api(
            endpoint=f"market/plugins/{plugin_id}",
            cache_key=f"plugin_{plugin_id}"
        )
    
    @staticmethod
    def purchase_plugin(plugin_id: str, payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """Purchase a plugin."""
        return call_api(
            endpoint=f"market/plugins/{plugin_id}/purchase",
            method="POST",
            data=payment_details
        )

class UserAPI:
    """User management API wrapper"""
    
    @staticmethod
    def get_current_user() -> Dict[str, Any]:
        """Get the current user information."""
        return call_api(
            endpoint="users/me",
            cache_key="current_user"
        )
    
    @staticmethod
    def update_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings."""
        return call_api(
            endpoint="users/settings",
            method="PUT",
            data=settings
        )

# Export domain-specific APIs
marketplace = MarketplaceAPI
users = UserAPI