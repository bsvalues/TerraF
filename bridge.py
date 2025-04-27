"""
TerraFusion Bridge Module

This module serves as a bridge between the Python Streamlit application
and the TypeScript/JavaScript backend. It provides functions to interact with
the Express API server from Python code.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, Union, List

# Default configuration
DEFAULT_API_URL = "http://localhost:5001"
API_URL = os.environ.get("TF_API_URL", DEFAULT_API_URL)

class TerraFusionBridge:
    """
    Bridge class to connect Python code with TerraFusion API services.
    """
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the bridge with API URL.
        
        Args:
            api_url: Base URL for the API. If not provided, uses environment variable 
                    TF_API_URL or falls back to default (http://localhost:5001)
        """
        self.api_url = api_url or API_URL
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        Get the API server status.
        
        Returns:
            Dict containing API status information.
        """
        try:
            response = requests.get(f"{self.api_url}/api/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Failed to connect to API: {str(e)}",
                "timestamp": None
            }
    
    def calculate_property_levy(self, property_id: Union[str, int]) -> Dict[str, Any]:
        """
        Calculate the levy for a property.
        
        Args:
            property_id: ID of the property to calculate levy for.
            
        Returns:
            Dict containing levy calculation result.
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/levy", 
                params={"propertyId": str(property_id)}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Failed to calculate levy: {str(e)}",
                "timestamp": None
            }

# Create a singleton instance for easy import
bridge = TerraFusionBridge()

# Helper function to get a new instance with custom configuration
def get_bridge(api_url: Optional[str] = None) -> TerraFusionBridge:
    """
    Get a new bridge instance with custom configuration.
    
    Args:
        api_url: Base URL for the API.
        
    Returns:
        TerraFusionBridge instance.
    """
    return TerraFusionBridge(api_url)