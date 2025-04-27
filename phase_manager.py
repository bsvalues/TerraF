"""
TerraFusion Platform Phase Manager Module

This module handles the persistence of phase data for TerraFusion projects.
It provides functionality to load, save, and update phase states.
"""

import json
import os

PHASES_DIR = "phases"
DEFAULT_PHASES = {
    "planning": {"name": "Planning", "completed": False, "progress": 0},
    "solution_design": {"name": "Solution Design", "completed": False, "progress": 0},
    "ticket_breakdown": {"name": "Ticket Breakdown", "completed": False, "progress": 0},
    "implementation": {"name": "Implementation", "completed": False, "progress": 0},
    "testing": {"name": "Testing", "completed": False, "progress": 0},
    "reporting": {"name": "Reporting", "completed": False, "progress": 0}
}

def load_phase_state(project_name):
    """
    Load phase state for a project. Creates default if doesn't exist.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Dictionary containing the phase data
    """
    path = os.path.join(PHASES_DIR, f"{project_name}_phases.json")
    if not os.path.exists(path):
        save_phase_state(project_name, DEFAULT_PHASES)  # Create initial
        return DEFAULT_PHASES
    with open(path, "r") as f:
        return json.load(f)

def save_phase_state(project_name, phase_data):
    """
    Save phase state for a project.
    
    Args:
        project_name: Name of the project
        phase_data: Dictionary containing the phase data
    """
    if not os.path.exists(PHASES_DIR):
        os.makedirs(PHASES_DIR)
    path = os.path.join(PHASES_DIR, f"{project_name}_phases.json")
    with open(path, "w") as f:
        json.dump(phase_data, f, indent=4)

def complete_phase(project_name, phase_key):
    """
    Mark a phase as completed.
    
    Args:
        project_name: Name of the project
        phase_key: Key of the phase to mark as completed
        
    Raises:
        ValueError: If the phase doesn't exist
    """
    phases = load_phase_state(project_name)
    if phase_key in phases:
        phases[phase_key]["completed"] = True
        phases[phase_key]["progress"] = 100
        save_phase_state(project_name, phases)
    else:
        raise ValueError(f"Phase '{phase_key}' does not exist.")

def update_phase_progress(project_name, phase_key, progress):
    """
    Update the progress percentage of a phase.
    
    Args:
        project_name: Name of the project
        phase_key: Key of the phase to update
        progress: New progress percentage (0-100)
        
    Raises:
        ValueError: If the phase doesn't exist or progress is invalid
    """
    if not 0 <= progress <= 100:
        raise ValueError("Progress must be between 0 and 100")
        
    phases = load_phase_state(project_name)
    if phase_key in phases:
        phases[phase_key]["progress"] = progress
        # If progress is 100, mark as completed
        if progress == 100:
            phases[phase_key]["completed"] = True
        save_phase_state(project_name, phases)
    else:
        raise ValueError(f"Phase '{phase_key}' does not exist.")

def get_next_phase(project_name, current_phase):
    """
    Get the next phase after the current one.
    
    Args:
        project_name: Name of the project
        current_phase: Key of the current phase
        
    Returns:
        Key of the next phase, or None if current phase is the last one
    """
    phases = load_phase_state(project_name)
    ordered_phases = list(phases.keys())
    
    try:
        current_index = ordered_phases.index(current_phase)
        if current_index < len(ordered_phases) - 1:
            return ordered_phases[current_index + 1]
    except ValueError:
        pass
        
    return None