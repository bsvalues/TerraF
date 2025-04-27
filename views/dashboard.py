"""
TerraFusionPlatform Dashboard View

This module handles the display and interaction for the project dashboard.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Union, Callable

# Import components and design system
from design_system import section_title, alert
from components import (
    display_metric_card, create_phase_progress_chart, display_task_suggestions
)

# Import state management
from state_manager import get_state_manager

# Import task suggestion functionality
from task_suggestion_agent import suggest_next_tasks

def display_dashboard() -> None:
    """Display the project dashboard view."""
    # Get state manager
    state_manager = get_state_manager()
    
    # Get phase data from state manager
    phase_data = state_manager.get_phase_data()
    metrics = state_manager.get_metrics()
    
    # Define phases - mapping from phase_id to display name
    phases = {
        "planning": "Planning",
        "solution_design": "Solution Design",
        "ticket_breakdown": "Ticket Breakdown",
        "implementation": "Implementation",
        "testing": "Testing",
        "reporting": "Reporting"
    }
    
    # Display dashboard title
    section_title("Project Dashboard", "Overview of project metrics and progress")
    
    # Create a dashboard layout with key metrics
    st.markdown("### Key Metrics")
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        display_metric_card(
            "Phases Completed", 
            f"{metrics['phases_completed']}/{len(phases)}"
        )
    
    with metric_col2:
        display_metric_card(
            "Reports Generated", 
            metrics["reports_generated"]
        )
    
    with metric_col3:
        display_metric_card(
            "Code Quality", 
            f"{metrics['code_quality']}%"
        )
    
    with metric_col4:
        display_metric_card(
            "Test Coverage", 
            f"{metrics['test_coverage']}%"
        )
    
    # Project Progress Section
    st.markdown("### Project Progress")
    
    # Create columns for the progress visualization
    progress_col1, progress_col2 = st.columns([3, 2])
    
    with progress_col1:
        # Create a phase progress chart
        fig = create_phase_progress_chart(phase_data, phases)
        st.plotly_chart(fig, use_container_width=True)
    
    with progress_col2:
        # Calculate overall project progress
        total_progress = sum(phase["progress"] for phase in phase_data.values())
        avg_progress = total_progress / len(phase_data) if phase_data else 0
        
        # Display overall progress with a big number
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background-color: rgba(124, 77, 255, 0.1); border-radius: 1rem; margin-bottom: 1rem;">
            <h3 style="margin-bottom: 1rem;">Overall Progress</h3>
            <div style="font-size: 3rem; font-weight: 700; color: #7c4dff;">{avg_progress:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Count completed phases
        completed_phases = sum(1 for phase in phase_data.values() if phase["completed"])
        
        # Display completion status
        st.markdown(f"""
        <div style="padding: 1rem; background-color: rgba(0, 230, 118, 0.1); border-radius: 0.5rem; border-left: 3px solid #00e676;">
            <strong>{completed_phases}</strong> of <strong>{len(phase_data)}</strong> phases completed
        </div>
        """, unsafe_allow_html=True)
    
    # Task Suggestion Section in Dashboard
    st.markdown("### 🧠 AI Task Suggestion Engine")
    
    # Create columns for task suggestions
    task_col1, task_col2 = st.columns([2, 1])
    
    with task_col1:
        # Get task suggestions based on current phase progress
        suggested_tasks = suggest_next_tasks(phase_data)
        display_task_suggestions(suggested_tasks)
    
    with task_col2:
        st.markdown("""
        <div style="background-color: rgba(124, 77, 255, 0.08); border-radius: 0.5rem; padding: 1rem; height: 100%;">
            <h4 style="margin-top: 0;">AI Assistant Tips</h4>
            <ul style="padding-left: 1.5rem; margin-bottom: 0;">
                <li style="margin-bottom: 0.5rem;">Focus on completing the current phase before moving to the next</li>
                <li style="margin-bottom: 0.5rem;">Generate reports to document your progress</li>
                <li style="margin-bottom: 0.5rem;">Update phase progress as you complete tasks</li>
                <li style="margin-bottom: 0;">Check suggested tasks for guidance on next steps</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent Activity Section
    st.markdown("### Recent Activity")
    
    # Get recent reports
    reports = state_manager.get_reports()
    recent_reports = sorted(reports, key=lambda r: r["timestamp"], reverse=True)[:5]
    
    if not recent_reports:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background-color: #1e1e1e; border-radius: 0.5rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
            <p>No recent activity. Generate reports to see them here.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display recent activity as a timeline
        st.markdown("""
        <div class="timeline-container">
        """, unsafe_allow_html=True)
        
        for report in recent_reports:
            timestamp = report["timestamp"].strftime("%Y-%m-%d %H:%M")
            title = report["title"]
            phase = report["phase"]
            phase_name = phases.get(phase, phase.title())
            
            st.markdown(f"""
            <div class="timeline-item">
                <div style="font-weight: 600;">{title}</div>
                <div style="font-size: 0.8rem; margin-top: 0.25rem;">
                    <span style="color: rgba(124, 77, 255, 0.8);">{phase_name}</span> • {timestamp}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)