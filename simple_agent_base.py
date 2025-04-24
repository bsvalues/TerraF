"""
Simple Agent Base Module for Code Deep Dive Analyzer Demo

This module provides simplified base classes for agent demonstration purposes.
It does not require the protocol server or threading functionality.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentCategory:
    """Enum for agent categories"""
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    DEPENDENCY = "dependency"
    DATABASE = "database"
    INTEGRATION_TEST = "integration_test"
    DOCUMENTATION = "documentation"
    AI_INTEGRATION = "ai_integration"
    DATA_INTEGRATION = "data_integration"
    DOMAIN_EXPERT = "domain_expert"

class Agent(ABC):
    """
    Base class for all agents in the demo system.
    """
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Category this agent belongs to
            capabilities: List of capabilities this agent provides
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: The task to execute
        
        Returns:
            Dict containing the result of the task execution
        """
        pass