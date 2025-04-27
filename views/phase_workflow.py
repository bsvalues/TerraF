"""
TerraFusionPlatform Phase Workflow View

This module handles the display and interaction for the DevOps workflow phases.
"""

import streamlit as st
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable

# Import components and design system
from design_system import section_title, alert, loading_indicator
from components import (
    display_phase_indicator, display_phase_progress_bars, create_phase_status_chart,
    display_phase_actions, display_task_suggestions, display_phase_preview,
    create_report_generation_form
)

# Import state management
from state_manager import get_state_manager

# Import task suggestion functionality
from task_suggestion_agent import suggest_next_tasks, get_next_phase_preview

def create_sample_report(phase: str, title: str) -> str:
    """
    Create a sample report for the selected phase.
    
    Args:
        phase: Phase to create the report for
        title: Title of the report
        
    Returns:
        Path to the created report file
    """
    # Get state manager
    state_manager = get_state_manager()
    
    # Create phase directory if it doesn't exist
    phase_dir = os.path.join("exports", phase)
    os.makedirs(phase_dir, exist_ok=True)
    
    # Generate a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{title.lower().replace(' ', '_')}_{timestamp}.md"
    filepath = os.path.join(phase_dir, filename)
    
    # Create sample content based on the phase
    content = f"# {title}\n\n"
    
    if phase == "planning":
        content += """## Overview
This document outlines the current user experience issues, data flow patterns, and identified problems that will be addressed in this project.

## UX Audit Findings
- Inconsistent navigation patterns across pages
- Slow loading times for data-heavy dashboards
- Mobile responsiveness issues on property detail pages

## Data Flow Map
1. User authentication → Session management → Data access filtering
2. API requests → Caching layer → Database queries → Response formatting
3. Real-time updates → WebSocket notifications → UI refresh

## Problem List
1. User session termination during critical workflows
2. Inconsistent state management between front-end and back-end
3. Poor error handling for API timeout scenarios
"""
    elif phase == "solution_design":
        content += """## Proposed Solutions
This document outlines the design approach to solve the identified problems.

## New UX Plan
- Implement consistent navigation with breadcrumbs across all pages
- Implement progressive loading for data-heavy dashboards
- Design mobile-first responsive layouts for all screens

## Data Awareness Strategies
- Implement client-side state management with Redux
- Add comprehensive error boundaries and fallback UI components
- Create a central data synchronization service

## Technical Approach
- Refactor component architecture to use atomic design principles
- Implement WebSocket connection management with auto-reconnect
- Add data integrity verification between client and server states
"""
    elif phase == "ticket_breakdown":
        content += """## Task Breakdown
This document breaks down the implementation into specific, actionable tickets.

### Ticket 1: Implement consistent navigation system
**Description:** Create a unified navigation component with breadcrumbs
**Acceptance Criteria:**
- Navigation appears consistently across all pages
- Breadcrumbs show accurate location in app hierarchy
- Current location is visually highlighted

### Ticket 2: Create progressive loading for dashboards
**Description:** Implement skeleton loaders and progressive data display
**Acceptance Criteria:**
- Initial page load under 300ms
- Critical content visible first
- Clear loading states for pending data

### Ticket 3: Refactor state management
**Description:** Implement Redux for centralized state management
**Acceptance Criteria:**
- All app state flows through Redux
- DevTools show accurate state transitions
- Persistent states survive page refreshes
"""
    elif phase == "implementation":
        content += """## Implementation Details
This document details the actual code changes and implementation approach.

### Code Changes Overview
- Created new NavigationSystem component with breadcrumbs
- Implemented SkeletonLoader components for progressive loading
- Added Redux store configuration with middleware

### Implementation Approach
The implementation followed a component-first strategy, ensuring that each UI element was independently testable before integration. Web Socket connection management was refactored to include heartbeats and reconnection logic.

### Unit Tests
- Added tests for navigation state management
- Created tests for progressive loading behaviors
- Implemented state transition tests for Redux actions
"""
    elif phase == "testing":
        content += """## Testing Results
This document summarizes the testing approach and results.

### End-to-End Test Scenarios
1. Complete user workflow from login to dashboard to detail pages
2. Reconnection behavior during network interruptions
3. State persistence across page reloads

### Validation Results
- All workflows completed successfully with 50ms improvement in perceived load time
- Reconnection successful within 2 seconds of network restoration
- State correctly maintained after page refresh

### Performance Metrics
- Initial load time reduced by 37%
- Time to interactive improved by 42%
- Memory usage reduced by 15%
"""
    elif phase == "reporting":
        content += """## Project Completion Report
This document summarizes the project outcomes and next steps.

### Key Accomplishments
- Successfully implemented all planned features within estimated time
- Achieved 40% improvement in overall user experience metrics
- Reduced error rates by 75% for critical workflows

### Lessons Learned
- Progressive loading strategy proved highly effective
- State management refactoring took longer than estimated but delivered higher value
- Component-first approach accelerated testing and integration

### Future Recommendations
- Apply the same navigation pattern to admin interfaces
- Consider extracting the WebSocket management into a reusable library
- Explore server-side rendering for further performance improvements
"""
    
    # Write the content to the file
    with open(filepath, 'w') as f:
        f.write(content)
    
    # Add the report to the state manager
    state_manager.add_report(phase, title, filename, filepath)
    
    return filepath

def handle_report_generation(phase: str, title: str) -> None:
    """
    Handle the generation of a new report.
    
    Args:
        phase: Phase to create the report for
        title: Title of the report
    """
    with st.spinner(f"Generating report: {title}"):
        report_path = create_sample_report(phase, title)
        st.success(f"Report created: {title}")

def display_phase_workflow() -> None:
    """Display the DevOps workflow phase view."""
    # Get state manager
    state_manager = get_state_manager()
    
    # Get phase data from state manager
    phase_data = state_manager.get_phase_data()
    current_phase = state_manager.get_current_phase()
    phase_statuses = state_manager.get_phase_statuses()
    
    # Define phases - mapping from phase_id to display name
    phases = {
        "planning": "Planning",
        "solution_design": "Solution Design",
        "ticket_breakdown": "Ticket Breakdown",
        "implementation": "Implementation",
        "testing": "Testing",
        "reporting": "Reporting"
    }
    
    # Get current phase name
    current_phase_name = phases.get(current_phase, current_phase.title())
    
    # Phase descriptions for display
    phase_descriptions = {
        "planning": "This phase focuses on identifying current issues through UX audits, mapping data flows, and creating a prioritized problem list.",
        "solution_design": "In this phase, we design new UX plans, data awareness strategies, and technical approaches to solve the identified problems.",
        "ticket_breakdown": "This phase breaks down the solution into specific, actionable tickets with clear acceptance criteria.",
        "implementation": "During implementation, we make the actual code changes, write unit tests, and document the implementation approach.",
        "testing": "This phase involves end-to-end validation, testing all workflows, and measuring performance improvements.",
        "reporting": "The final phase includes creating completion reports, summarizing outcomes, and documenting lessons learned."
    }
    
    # Display phase indicator
    section_title("DevOps Workflow")
    display_phase_indicator(phases, current_phase)
    
    # Display phase progress
    st.markdown("### Phase Progress")
    display_phase_progress_bars(phase_data, phases, phase_statuses)
    
    # Current phase content
    st.markdown(f"## Current Phase: {current_phase_name}")
    st.markdown(f"*{phase_descriptions.get(current_phase, 'No description available.')}*")
    
    # Create columns for actions and reports
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Phase Visualization")
        
        # Create and display a chart for phase status
        fig = create_phase_status_chart(phase_statuses, phases)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Actions")
        display_phase_actions(current_phase)
        
        # Phase control buttons
        st.markdown("### Phase Controls")
        
        # Create a two-column layout for buttons
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            # Current phase progress controls
            st.markdown("#### Update Progress")
            
            # Check if we have loading state
            is_updating = state_manager.is_loading(f"update_phase_{current_phase}")
            has_error = state_manager.has_error(f"update_phase_{current_phase}")
            
            progress_value = st.slider(
                "Progress", 
                0, 100, 
                phase_data[current_phase]["progress"], 
                5,
                disabled=is_updating
            )
            
            if st.button("Update Progress", disabled=is_updating):
                success = state_manager.update_phase_progress(current_phase, progress_value)
                if success:
                    st.success(f"Progress updated to {progress_value}%")
                    st.rerun()
            
            # Display error if we have one
            if has_error:
                error_message = state_manager.get_error(f"update_phase_{current_phase}")
                st.error(f"Error: {error_message}")
        
        with button_col2:
            # Phase completion control
            st.markdown("#### Complete Phase")
            
            # Check if we have loading state
            is_completing = state_manager.is_loading("complete_phase")
            has_completion_error = state_manager.has_error("complete_phase")
            
            if st.button("Mark Phase as Complete", disabled=is_completing):
                success = state_manager.complete_current_phase()
                if success:
                    st.success(f"Phase {current_phase_name} marked as complete!")
                    st.rerun()
            
            # Display error if we have one
            if has_completion_error:
                error_message = state_manager.get_error("complete_phase")
                st.error(f"Error: {error_message}")
    
    with col2:
        st.markdown("### Report Generation")
        
        # Report generation form
        create_report_generation_form(
            current_phase,
            handle_report_generation
        )
        
        # Task Suggestion Agent Section
        st.markdown("### 🧠 Task Suggestion Engine")
        
        # Get task suggestions based on current phase progress
        suggested_tasks = suggest_next_tasks(phase_data)
        display_task_suggestions(suggested_tasks)
        
        # Show preview of next phase
        next_phase_preview = get_next_phase_preview(phase_data)
        display_phase_preview(next_phase_preview)