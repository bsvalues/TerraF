"""
TerraFusionPlatform State Manager

This module provides centralized state management for the application,
ensuring consistent data flow and state updates throughout the platform.
"""

import json
import os
import time
from datetime import datetime
import streamlit as st
from typing import Dict, List, Any, Optional, Union
import logging

# Import existing phase management functionality
from phase_manager import load_phase_state, save_phase_state, complete_phase, update_phase_progress, get_next_phase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StateManager:
    """
    Central state manager for the TerraFusionPlatform.
    
    This class handles state loading, updating, and persistence across the application.
    It provides a unified interface for state management and ensures data consistency.
    """
    
    def __init__(self, project_name: str = "terra_fusion_platform"):
        """
        Initialize the state manager.
        
        Args:
            project_name: Name of the current project
        """
        self.project_name = project_name
        self.last_updated = datetime.now()
        self.loading_states: Dict[str, bool] = {}
        self.error_states: Dict[str, Optional[str]] = {}
        
        # Load the initial state
        self._initialize_state()
        
        logger.info("StateManager initialized for project: %s", project_name)
    
    def _initialize_state(self):
        """Initialize all application state components."""
        # Initialize phase data
        self.phase_data = load_phase_state(self.project_name)
        
        # Calculate derived state
        self._calculate_derived_state()
        
        # Initialize reports if needed
        if not hasattr(st.session_state, 'reports'):
            st.session_state.reports = []
        
        # Initialize metrics if needed
        if not hasattr(st.session_state, 'metrics'):
            st.session_state.metrics = {
                "reports_generated": 0,
                "phases_completed": 0,
                "test_coverage": 0,
                "code_quality": 0
            }
    
    def _calculate_derived_state(self):
        """Calculate derived state based on the current phase data."""
        # Determine current phase
        self.current_phase = "planning"  # Default
        
        # Find the first incomplete phase
        for phase_id, phase_info in self.phase_data.items():
            if not phase_info["completed"]:
                self.current_phase = phase_id
                break
        
        # Calculate phase statuses
        self.phase_statuses = {}
        for phase_id, phase_info in self.phase_data.items():
            if phase_info["completed"]:
                self.phase_statuses[phase_id] = "completed"
            elif phase_id == self.current_phase:
                self.phase_statuses[phase_id] = "in_progress"
            else:
                self.phase_statuses[phase_id] = "pending"
    
    def get_phase_data(self) -> Dict[str, Any]:
        """Get the current phase data."""
        return self.phase_data
    
    def get_current_phase(self) -> str:
        """Get the current active phase ID."""
        return self.current_phase
    
    def get_phase_statuses(self) -> Dict[str, str]:
        """Get the status of all phases."""
        return self.phase_statuses
    
    def update_phase_progress(self, phase_id: str, progress: int) -> bool:
        """
        Update the progress of a specific phase.
        
        Args:
            phase_id: ID of the phase to update
            progress: New progress value (0-100)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Set loading state
            self.set_loading_state(f"update_phase_{phase_id}", True)
            
            # Clear any existing errors
            self.clear_error(f"update_phase_{phase_id}")
            
            # Update the phase progress
            update_phase_progress(self.project_name, phase_id, progress)
            
            # Reload phase data and recalculate derived state
            self.phase_data = load_phase_state(self.project_name)
            self._calculate_derived_state()
            
            # Update last updated timestamp
            self.last_updated = datetime.now()
            
            logger.info("Updated progress for phase %s to %d%%", phase_id, progress)
            return True
        except Exception as e:
            # Set error state
            error_message = f"Failed to update phase progress: {str(e)}"
            self.set_error(f"update_phase_{phase_id}", error_message)
            logger.error(error_message)
            return False
        finally:
            # Clear loading state
            self.set_loading_state(f"update_phase_{phase_id}", False)
    
    def complete_current_phase(self) -> bool:
        """
        Mark the current phase as completed and advance to the next phase.
        
        Returns:
            bool: True if completion was successful, False otherwise
        """
        try:
            # Set loading state
            self.set_loading_state("complete_phase", True)
            
            # Clear any existing errors
            self.clear_error("complete_phase")
            
            current_phase = self.current_phase
            
            # Complete the current phase
            complete_phase(self.project_name, current_phase)
            
            # Get the next phase
            next_phase = get_next_phase(self.project_name, current_phase)
            
            # Update metrics
            self.update_metric("phases_completed", st.session_state.metrics["phases_completed"] + 1)
            
            # Reload phase data and recalculate derived state
            self.phase_data = load_phase_state(self.project_name)
            self._calculate_derived_state()
            
            # Update last updated timestamp
            self.last_updated = datetime.now()
            
            logger.info("Completed phase %s, next phase: %s", current_phase, next_phase)
            return True
        except Exception as e:
            # Set error state
            error_message = f"Failed to complete current phase: {str(e)}"
            self.set_error("complete_phase", error_message)
            logger.error(error_message)
            return False
        finally:
            # Clear loading state
            self.set_loading_state("complete_phase", False)
    
    def add_report(self, phase: str, title: str, filename: str, path: str) -> None:
        """
        Add a new report to the reports list.
        
        Args:
            phase: Phase the report belongs to
            title: Report title
            filename: Report filename
            path: Path to the report file
        """
        if not hasattr(st.session_state, 'reports'):
            st.session_state.reports = []
        
        new_report = {
            "phase": phase,
            "title": title,
            "timestamp": datetime.now(),
            "filename": filename,
            "path": path
        }
        
        st.session_state.reports.append(new_report)
        self.update_metric("reports_generated", st.session_state.metrics["reports_generated"] + 1)
        
        logger.info("Added new report: %s for phase %s", title, phase)
    
    def get_reports(self, phase_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all reports, optionally filtered by phase.
        
        Args:
            phase_filter: Optional phase to filter reports by
            
        Returns:
            List of report dictionaries
        """
        if not hasattr(st.session_state, 'reports'):
            return []
        
        if phase_filter:
            return [r for r in st.session_state.reports if r["phase"] == phase_filter]
        else:
            return st.session_state.reports
    
    def get_metrics(self) -> Dict[str, Union[int, float]]:
        """Get the current metrics."""
        return st.session_state.metrics
    
    def update_metric(self, metric_name: str, value: Union[int, float]) -> None:
        """
        Update a specific metric.
        
        Args:
            metric_name: Name of the metric to update
            value: New value for the metric
        """
        if metric_name in st.session_state.metrics:
            st.session_state.metrics[metric_name] = value
            logger.info("Updated metric %s to %s", metric_name, value)
    
    def set_loading_state(self, key: str, is_loading: bool) -> None:
        """
        Set the loading state for a specific operation.
        
        Args:
            key: Identifier for the operation
            is_loading: True if operation is loading, False otherwise
        """
        self.loading_states[key] = is_loading
    
    def is_loading(self, key: str) -> bool:
        """
        Check if an operation is in loading state.
        
        Args:
            key: Identifier for the operation
            
        Returns:
            bool: True if operation is loading, False otherwise
        """
        return self.loading_states.get(key, False)
    
    def set_error(self, key: str, error_message: str) -> None:
        """
        Set an error state for a specific operation.
        
        Args:
            key: Identifier for the operation
            error_message: Error message
        """
        self.error_states[key] = error_message
    
    def clear_error(self, key: str) -> None:
        """
        Clear the error state for a specific operation.
        
        Args:
            key: Identifier for the operation
        """
        if key in self.error_states:
            self.error_states[key] = None
    
    def get_error(self, key: str) -> Optional[str]:
        """
        Get the error message for a specific operation.
        
        Args:
            key: Identifier for the operation
            
        Returns:
            Optional[str]: Error message if one exists, None otherwise
        """
        return self.error_states.get(key)
    
    def has_error(self, key: str) -> bool:
        """
        Check if an operation has an error.
        
        Args:
            key: Identifier for the operation
            
        Returns:
            bool: True if operation has an error, False otherwise
        """
        return self.error_states.get(key) is not None
    
    def reset_errors(self) -> None:
        """Clear all error states."""
        self.error_states = {}
    
    def get_last_updated(self) -> datetime:
        """Get the timestamp of the last state update."""
        return self.last_updated


# Singleton instance of the StateManager
_state_manager_instance = None

def get_state_manager(force_refresh=False) -> StateManager:
    """
    Get or create the singleton StateManager instance.
    
    Args:
        force_refresh: Force a refresh of the state manager
        
    Returns:
        StateManager instance
    """
    global _state_manager_instance
    
    if _state_manager_instance is None or force_refresh:
        project_name = st.session_state.get("project_name", "terra_fusion_platform")
        _state_manager_instance = StateManager(project_name)
    
    return _state_manager_instance


# Initialize state manager in session state if needed
def initialize_state_management():
    """Initialize the state management system."""
    if 'state_manager_initialized' not in st.session_state:
        # Initialize a project name if not already set
        if 'project_name' not in st.session_state:
            st.session_state.project_name = "terra_fusion_platform"
            
        # Create the state manager
        state_manager = get_state_manager(force_refresh=True)
        
        # Mark as initialized
        st.session_state.state_manager_initialized = True
        
        logger.info("State management system initialized")
        
        return state_manager
    else:
        return get_state_manager()