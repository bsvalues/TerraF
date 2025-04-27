"""
TerraFusion Platform Task Suggestion Agent

This module provides AI-driven task suggestions based on the current project phase states.
It analyzes phase progress and provides relevant, actionable next steps.
"""

def suggest_next_tasks(phases):
    """
    Takes current phase states and suggests next logical development tasks.
    
    Args:
        phases: Dictionary of phase data with completion status
        
    Returns:
        List of suggested next tasks based on project state
    """
    # Analyze phases
    completed_phases = [phase_id for phase_id, phase_data in phases.items() if phase_data["completed"]]
    current_phases = [phase_id for phase_id, phase_data in phases.items() 
                     if not phase_data["completed"] and phase_data["progress"] > 0]
    
    if not current_phases:
        if len(completed_phases) == len(phases):
            return ["🎉 All phases completed! Prepare final deployment and retrospective meeting."]
        else:
            # Find the first incomplete phase
            for phase_id in phases:
                if not phases[phase_id]["completed"]:
                    current_phases = [phase_id]
                    break
    
    # Get suggestions for current phases
    all_suggestions = []
    
    # Map phase_ids to friendly names for suggestion lookup
    phase_name_map = {
        "planning": "Planning",
        "solution_design": "Solution Design",
        "ticket_breakdown": "Ticket Breakdown",
        "implementation": "Implementation",
        "testing": "Testing",
        "reporting": "Reporting"
    }
    
    # Define suggestions for each phase
    suggestions = {
        "Planning": [
            "🔎 Complete UX audit to identify interface pain points",
            "📝 Create detailed data flow maps for the system",
            "📋 Create a prioritized problem list to address"
        ],
        "Solution Design": [
            "🛠 Design new user experience plans and wireframes",
            "📊 Develop data awareness strategies for better state management",
            "⚙️ Document the technical approach for implementation"
        ],
        "Ticket Breakdown": [
            "📌 Break down features into actionable tickets",
            "✅ Define clear acceptance criteria for each task",
            "⏱️ Estimate effort for implementation tasks"
        ],
        "Implementation": [
            "💻 Implement code changes according to tickets",
            "🧪 Write unit tests for new functionality",
            "📝 Document the implementation details and approach"
        ],
        "Testing": [
            "🔍 Perform end-to-end testing of workflows",
            "✅ Validate changes against acceptance criteria",
            "📊 Measure and document performance improvements"
        ],
        "Reporting": [
            "📑 Create a comprehensive project completion report",
            "📝 Document lessons learned throughout the project",
            "🚀 Provide recommendations for future enhancements"
        ]
    }
    
    # Add suggestions for current phases
    for phase_id in current_phases:
        phase_name = phase_name_map.get(phase_id, phase_id)
        phase_suggestions = suggestions.get(phase_name, ["📋 No specific suggestions available for this phase."])
        
        # Calculate how many suggestions to show based on progress
        progress = phases[phase_id]["progress"]
        if progress < 30:
            # Early in the phase, show all suggestions
            all_suggestions.extend(phase_suggestions)
        elif progress < 60:
            # Mid-phase, focus on middle and later tasks
            all_suggestions.extend(phase_suggestions[1:])
        else:
            # Late in the phase, focus on final tasks
            all_suggestions.append(phase_suggestions[-1])
            all_suggestions.append("✨ Prepare to complete this phase and move to the next")
    
    # If we have no suggestions yet, provide a default
    if not all_suggestions:
        all_suggestions = ["📋 Start work on the first phase to get specific suggestions."]
    
    return all_suggestions


def get_next_phase_preview(phases):
    """
    Provides a preview of what's coming in the next phase.
    
    Args:
        phases: Dictionary of phase data
        
    Returns:
        String description of the next phase or None if all phases are completed
    """
    # Find the current active phase
    current_phase = None
    for phase_id, phase_data in phases.items():
        if not phase_data["completed"] and phase_data["progress"] > 0:
            current_phase = phase_id
            break
    
    if not current_phase:
        return None
    
    # Define the order of phases
    phase_order = ["planning", "solution_design", "ticket_breakdown", "implementation", "testing", "reporting"]
    
    # Find the current phase index
    try:
        current_index = phase_order.index(current_phase)
    except ValueError:
        return None
    
    # If this is the last phase, there's no next phase
    if current_index >= len(phase_order) - 1:
        return None
    
    # Get the next phase
    next_phase = phase_order[current_index + 1]
    
    # Map of phase descriptions
    phase_descriptions = {
        "planning": "You'll be defining the solution approach and overall architecture.",
        "solution_design": "You'll break down the solution into specific implementation tickets.",
        "ticket_breakdown": "You'll implement the solution according to your tickets.",
        "implementation": "You'll test the implementation to ensure it meets requirements.",
        "testing": "You'll document outcomes and prepare final project reports.",
        "reporting": "All phases will be complete!"
    }
    
    return f"Coming next: **{next_phase.replace('_', ' ').title()}** phase - {phase_descriptions.get(next_phase, '')}"