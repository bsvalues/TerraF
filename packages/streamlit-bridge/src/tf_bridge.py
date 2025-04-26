"""
TerraFusion Bridge Module

This module provides a bridge for connecting Streamlit apps to the 
Node.js/Express backend of the TerraFusion platform.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for API calls
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:4000")
REQUEST_TIMEOUT = 30  # seconds

def call_api(
    path: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = REQUEST_TIMEOUT
) -> Dict[str, Any]:
    """
    Make an API call to the TerraFusion backend.
    
    Args:
        path: The API endpoint path (e.g., "/api/v1/levy")
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional request body for POST/PUT requests
        headers: Optional HTTP headers
        params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Response data as a dictionary
        
    Raises:
        Exception: If the API call fails
    """
    # Ensure path starts with a slash
    if not path.startswith('/'):
        path = f"/{path}"
        
    # Construct full URL
    url = f"{API_BASE_URL}{path}"
    
    # Default headers
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Add custom headers if provided
    if headers:
        request_headers.update(headers)
        
    logger.info(f"Calling API: {method} {url}")
    
    try:
        # Make the request
        response = requests.request(
            method=method,
            url=url,
            json=data if data else None,
            headers=request_headers,
            params=params,
            timeout=timeout
        )
        
        # Raise an exception for HTTP errors
        response.raise_for_status()
        
        # Return JSON response
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"Error response: {error_data}")
            except ValueError:
                logger.error(f"Error content: {e.response.text}")
        raise Exception(f"API request failed: {str(e)}")