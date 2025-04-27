"""
TerraFusionPlatform ICSF AI-Driven DevOps Framework (Enhanced Version)

A comprehensive interface for managing AI-powered code analysis and deployment workflows.
"""

import streamlit as st
import os
import subprocess
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import random

# Configure the Streamlit page
st.set_page_config(
    page_title="TerraFusionPlatform ICSF",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define CSS styling for our app
st.markdown("""
<style>
    /* General styling */
    .main {
        background-color: #121212;
        color: #f8f9fa;
    }
    
    /* Header styling */
    .header {
        color: #7c4dff;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .subheader {
        color: rgba(248, 249, 250, 0.85);
        font-size: 1.2rem;
        margin-bottom: 1.5rem;
    }
    
    /* Card styling */
    .tf-card {
        background-color: #1e1e1e;
        border: 1px solid rgba(124, 77, 255, 0.25);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        transition: transform 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .tf-card:hover {
        transform: translateY(-2px);
    }
    
    /* Phase indicator styling */
    .phase-indicator {
        display: flex;
        margin-bottom: 1.5rem;
    }
    
    .phase-item {
        flex: 1;
        text-align: center;
        padding: 0.5rem 0;
        position: relative;
        background-color: #252525;
        border: 1px solid rgba(124, 77, 255, 0.1);
    }
    
    .phase-item.active {
        background-color: rgba(124, 77, 255, 0.12);
        border-color: #7c4dff;
        color: #7c4dff;
        font-weight: 600;
    }
    
    .phase-item:not(:last-child):after {
        content: "";
        position: absolute;
        right: -15px;
        top: 50%;
        transform: translateY(-50%);
        width: 30px;
        height: 2px;
        background-color: rgba(124, 77, 255, 0.25);
        z-index: 1;
    }
    
    /* Report card styling */
    .report-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #252525;
        margin-bottom: 0.75rem;
        border-left: 3px solid #7c4dff;
    }
    
    /* Button styling */
    .primary-button {
        background-color: #7c4dff;
        color: white;
        border-radius: 0.375rem;
        border: none;
        padding: 0.6rem 1.25rem;
        font-weight: 500;
        transition: all 250ms;
    }
    
    .primary-button:hover {
        background-color: #b47cff;
        transform: translateY(-2px);
    }
    
    /* Alert styling */
    .tf-alert {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        position: relative;
    }
    
    .tf-alert.success {
        background-color: rgba(0, 230, 118, 0.1);
        border-left: 3px solid #00e676;
    }
    
    .tf-alert.warning {
        background-color: rgba(255, 234, 0, 0.1);
        border-left: 3px solid #ffea00;
    }
    
    .tf-alert.error {
        background-color: rgba(255, 23, 68, 0.1);
        border-left: 3px solid #ff1744;
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-success {
        background-color: #00e676;
        box-shadow: 0 0 8px #00e676;
    }
    
    .status-warning {
        background-color: #ffea00;
        box-shadow: 0 0 8px #ffea00;
    }
    
    .status-error {
        background-color: #ff1744;
        box-shadow: 0 0 8px #ff1744;
    }
    
    /* Timeline styling */
    .timeline-container {
        position: relative;
        margin-left: 2rem;
        padding-left: 2rem;
        border-left: 2px solid rgba(124, 77, 255, 0.25);
    }
    
    .timeline-item {
        position: relative;
        margin-bottom: 1.5rem;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -2.3rem;
        top: 6px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #7c4dff;
        box-shadow: 0 0 8px rgba(124, 77, 255, 0.3);
    }
    
    /* Table styling */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    
    th {
        background-color: #303030;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
    }
    
    td {
        padding: 0.75rem;
        border-top: 1px solid rgba(124, 77, 255, 0.1);
    }
    
    tr:hover td {
        background-color: rgba(124, 77, 255, 0.05);
    }
    
    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    .logo-text {
        font-size: 1.5rem;
        font-weight: 700;
        margin-left: 0.75rem;
        background: linear-gradient(90deg, #7c4dff, #00e0e0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Import phase manager and task suggestion agent
from phase_manager import load_phase_state, save_phase_state, complete_phase, update_phase_progress, get_next_phase
from task_suggestion_agent import suggest_next_tasks, get_next_phase_preview

# Initialize project name
if 'project_name' not in st.session_state:
    st.session_state.project_name = "terra_fusion_platform"

# Initialize session state for workflow status with persistent storage
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = "planning"
    
# Load phases from storage
if 'phase_data' not in st.session_state:
    st.session_state.phase_data = load_phase_state(st.session_state.project_name)
    
# Initialize phase statuses based on the loaded data
if 'phase_statuses' not in st.session_state:
    st.session_state.phase_statuses = {}
    for phase_key, phase_info in st.session_state.phase_data.items():
        if phase_info["completed"]:
            st.session_state.phase_statuses[phase_key] = "completed"
        elif phase_key == st.session_state.current_phase:
            st.session_state.phase_statuses[phase_key] = "in_progress"
        else:
            st.session_state.phase_statuses[phase_key] = "pending"
    
if 'reports' not in st.session_state:
    st.session_state.reports = []
    
if 'metrics' not in st.session_state:
    st.session_state.metrics = {
        "reports_generated": 0,
        "phases_completed": 0,
        "test_coverage": 0,
        "code_quality": 0
    }

# Helper functions
def get_phase_files(phase):
    """Get all markdown files for a specific phase."""
    phase_dir = os.path.join("exports", phase)
    if not os.path.exists(phase_dir):
        return []
    return [f for f in os.listdir(phase_dir) if f.endswith('.md') and os.path.isfile(os.path.join(phase_dir, f))]

def get_all_report_files():
    """Get all report files from all phases."""
    all_files = []
    for phase in ["planning", "solution_design", "ticket_breakdown", "implementation", "testing", "reporting", "misc"]:
        phase_dir = os.path.join("exports", phase)
        if os.path.exists(phase_dir):
            phase_files = get_phase_files(phase)
            all_files.extend([(phase, f) for f in phase_files])
    return all_files

def run_script(script_path):
    """Run a Python script and return the output."""
    try:
        result = subprocess.run(['python3', script_path], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error running script: {str(e)}"

def create_sample_report(phase, title):
    """Create a sample report for the selected phase."""
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
        
    # Update the reports list in session state
    if 'reports' not in st.session_state:
        st.session_state.reports = []
    
    st.session_state.reports.append({
        "phase": phase,
        "title": title,
        "timestamp": datetime.now(),
        "filename": filename,
        "path": filepath
    })
    
    # Update metrics
    st.session_state.metrics["reports_generated"] += 1
    
    # Simulate some code quality and test coverage improvements
    if phase == "implementation":
        st.session_state.metrics["code_quality"] = min(100, st.session_state.metrics["code_quality"] + random.randint(5, 15))
    elif phase == "testing":
        st.session_state.metrics["test_coverage"] = min(100, st.session_state.metrics["test_coverage"] + random.randint(10, 20))
    
    return filepath

def complete_current_phase():
    """Mark the current phase as completed and advance to the next phase."""
    current_phase = st.session_state.current_phase
    
    # Update phase statuses in session
    st.session_state.phase_statuses[current_phase] = "completed"
    
    # Update persistent storage
    complete_phase(st.session_state.project_name, current_phase)
    
    # Update metrics
    st.session_state.metrics["phases_completed"] += 1
    
    # Get the next phase using phase manager
    next_phase = get_next_phase(st.session_state.project_name, current_phase)
    
    if next_phase:
        # Update session state
        st.session_state.current_phase = next_phase
        st.session_state.phase_statuses[next_phase] = "in_progress"
        
        # Update progress in persistent storage
        phase_data = st.session_state.phase_data
        phase_data[next_phase]["progress"] = 20  # Start with some progress
        save_phase_state(st.session_state.project_name, phase_data)
        st.session_state.phase_data = phase_data
    
    # If we completed the final phase, generate the PR
    if current_phase == "reporting":
        run_script("batch_pr_generator.py")
        st.session_state.pr_generated = True
        
    # Reload phase data from storage
    st.session_state.phase_data = load_phase_state(st.session_state.project_name)

def get_report_stats():
    """Get statistics about reports."""
    all_files = get_all_report_files()
    stats = {}
    
    for phase in ["planning", "solution_design", "ticket_breakdown", "implementation", "testing", "reporting"]:
        stats[phase] = len([f for p, f in all_files if p == phase])
    
    return stats

# Sidebar navigation
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <div style="font-size: 2rem;">🚀</div>
        <div class="logo-text">TerraFusionPlatform</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ICSF AI-Driven DevOps")
    
    # Display phase progress
    phases = {
        "planning": "Planning",
        "solution_design": "Solution Design",
        "ticket_breakdown": "Ticket Breakdown",
        "implementation": "Implementation",
        "testing": "Testing",
        "reporting": "Reporting"
    }
    
    for phase_id, phase_name in phases.items():
        status = st.session_state.phase_statuses[phase_id]
        is_current = phase_id == st.session_state.current_phase
        
        if status == "completed":
            icon = "✅"
        elif status == "in_progress":
            icon = "🔄"
        else:
            icon = "⏳"
            
        if is_current:
            st.sidebar.markdown(f"**{icon} {phase_name}**")
        else:
            st.sidebar.markdown(f"{icon} {phase_name}")
    
    st.sidebar.divider()
    
    # Organization tools
    st.sidebar.markdown("### Tools")
    
    if st.sidebar.button("Organize Reports", key="organize"):
        with st.spinner("Organizing reports..."):
            output = run_script("auto_folder_md_reports.py")
            st.sidebar.success("Reports organized successfully!")
    
    if st.sidebar.button("Generate PR Description", key="generate_pr"):
        with st.spinner("Generating PR description..."):
            output = run_script("batch_pr_generator.py")
            st.sidebar.success("PR description generated successfully!")
    
    if st.sidebar.button("Generate Test Reports", key="generate_test"):
        with st.spinner("Generating test reports..."):
            output = run_script("generate_test_reports.py")
            st.sidebar.success("Test reports generated successfully!")
    
    st.sidebar.divider()
    
    # System status
    st.sidebar.markdown("### System Status")
    
    st.sidebar.markdown("""
    <div style="display: flex; align-items: center; font-size: 0.8rem; color: rgba(248, 249, 250, 0.85);">
        <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #00e676; 
                   margin-right: 0.5rem; box-shadow: 0 0 5px #00e676;"></div>
        <div>System Online</div>
        <div style="margin-left: auto; font-size: 0.7rem; color: rgba(248, 249, 250, 0.65);">
            v1.1.0
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main content
st.markdown('<h1 class="header">TerraFusionPlatform ICSF AI-Driven DevOps Framework</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">A fully structured, autonomous environment for running high-quality, AI-assisted development workflows.</p>', unsafe_allow_html=True)

# Create tabs for different views
main_tabs = st.tabs(["DevOps Workflow", "Project Dashboard", "Reports"])

with main_tabs[0]:  # DevOps Workflow tab
    # Create phase indicator
    phase_html = '<div class="phase-indicator">'
    for phase_id, phase_name in phases.items():
        status_class = "active" if phase_id == st.session_state.current_phase else ""
        phase_html += f'<div class="phase-item {status_class}">{phase_name}</div>'
    phase_html += '</div>'
    
    st.markdown(phase_html, unsafe_allow_html=True)
    
    # Display phase progress from persistent storage
    st.markdown("### Phase Progress")
    for phase_id, phase_info in st.session_state.phase_data.items():
        phase_name = phases[phase_id]
        progress = phase_info["progress"]
        completed = phase_info["completed"]
        
        # Determine color based on status
        if completed:
            bar_color = "#00e676"  # Green for completed
        elif phase_id == st.session_state.current_phase:
            bar_color = "#7c4dff"  # Purple for in-progress
        else:
            bar_color = "#555555"  # Grey for pending
        
        # Create a custom progress bar with HTML/CSS
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>{phase_name}</span>
                <span>{progress}%</span>
            </div>
            <div style="height: 10px; background-color: #303030; border-radius: 5px; overflow: hidden;">
                <div style="height: 100%; width: {progress}%; background-color: {bar_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Current phase content
    current_phase = st.session_state.current_phase
    current_phase_name = phases[current_phase]
    
    st.markdown(f"## Current Phase: {current_phase_name}")
    
    # Display phase description based on the current phase
    phase_descriptions = {
        "planning": "This phase focuses on identifying current issues through UX audits, mapping data flows, and creating a prioritized problem list.",
        "solution_design": "In this phase, we design new UX plans, data awareness strategies, and technical approaches to solve the identified problems.",
        "ticket_breakdown": "This phase breaks down the solution into specific, actionable tickets with clear acceptance criteria.",
        "implementation": "During implementation, we make the actual code changes, write unit tests, and document the implementation approach.",
        "testing": "This phase involves end-to-end validation, testing all workflows, and measuring performance improvements.",
        "reporting": "The final phase includes creating completion reports, summarizing outcomes, and documenting lessons learned."
    }
    
    st.markdown(f"*{phase_descriptions[current_phase]}*")
    
    # Create columns for actions and reports
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Phase Visualization")
        
        # Create a visualization of the current phase progress
        phases_df = pd.DataFrame({
            'Phase': list(phases.values()),
            'Status': [st.session_state.phase_statuses[phase_id] for phase_id in phases.keys()],
            'Order': list(range(len(phases)))
        })
        
        # Create a color map for the phase statuses
        color_map = {
            'completed': '#00e676',
            'in_progress': '#7c4dff',
            'pending': '#303030'
        }
        
        # Create a horizontal bar chart for phase progress
        fig = px.bar(
            phases_df, 
            y='Phase', 
            x=[1] * len(phases_df),
            color='Status',
            color_discrete_map=color_map,
            orientation='h',
            height=240,
            text='Phase'
        )
        
        # Customize the layout
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(248,249,250,0.85)'),
            showlegend=True,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False
            ),
            yaxis=dict(
                autorange="reversed",
                showgrid=False,
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='relative'
        )
        
        # Update bar appearance
        fig.update_traces(
            marker_line_color='rgba(0,0,0,0)',
            marker_line_width=0,
            width=0.8,
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color='white')
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Actions")
        
        # Phase-specific actions
        action_card_html = '<div class="tf-card">'
        
        if current_phase == "planning":
            action_card_html += """
            <h3>Planning Phase Actions</h3>
            <p>Create the following documents to complete this phase:</p>
            <ul>
                <li>UX Audit - Document current user experience issues</li>
                <li>Data Flow Map - Map out how data moves through the system</li>
                <li>Problem List - Create a prioritized list of problems to solve</li>
            </ul>
            """
        elif current_phase == "solution_design":
            action_card_html += """
            <h3>Solution Design Actions</h3>
            <p>Design solutions for the identified problems:</p>
            <ul>
                <li>New UX Plan - Create wireframes and user flow diagrams</li>
                <li>Data Awareness Strategies - Design approaches for better state management</li>
                <li>Technical Approach - Document the implementation strategy</li>
            </ul>
            """
        elif current_phase == "ticket_breakdown":
            action_card_html += """
            <h3>Ticket Breakdown Actions</h3>
            <p>Break down the implementation into specific tasks:</p>
            <ul>
                <li>Create tickets with clear descriptions</li>
                <li>Define acceptance criteria for each ticket</li>
                <li>Estimate effort for implementation</li>
            </ul>
            """
        elif current_phase == "implementation":
            action_card_html += """
            <h3>Implementation Actions</h3>
            <p>Execute the implementation plan:</p>
            <ul>
                <li>Make code changes according to the tickets</li>
                <li>Write unit tests for new functionality</li>
                <li>Document the implementation approach</li>
            </ul>
            """
        elif current_phase == "testing":
            action_card_html += """
            <h3>Testing Actions</h3>
            <p>Validate the implemented changes:</p>
            <ul>
                <li>Perform end-to-end testing of workflows</li>
                <li>Validate against acceptance criteria</li>
                <li>Measure and document performance improvements</li>
            </ul>
            """
        elif current_phase == "reporting":
            action_card_html += """
            <h3>Reporting Actions</h3>
            <p>Summarize the project outcomes:</p>
            <ul>
                <li>Create a project completion report</li>
                <li>Document lessons learned</li>
                <li>Provide recommendations for future improvements</li>
            </ul>
            """
        
        action_card_html += '</div>'
        st.markdown(action_card_html, unsafe_allow_html=True)
        
        # Document creation form
        st.markdown("### Create New Document")
        
        with st.form("create_document_form"):
            doc_title = st.text_input("Document Title", f"New {current_phase_name} Document")
            submit_doc = st.form_submit_button("Create Document")
            
            if submit_doc:
                if doc_title:
                    with st.spinner("Creating document..."):
                        filepath = create_sample_report(current_phase, doc_title)
                        
                        # Update phase progress in persistent storage (increase by 20% for each doc, max 80%)
                        phase_data = st.session_state.phase_data
                        current_progress = phase_data[current_phase]["progress"]
                        new_progress = min(80, current_progress + 20)  # Max 80% before completion
                        phase_data[current_phase]["progress"] = new_progress
                        save_phase_state(st.session_state.project_name, phase_data)
                        st.session_state.phase_data = phase_data
                        
                        st.success(f"Document created: {doc_title}")
                else:
                    st.error("Please enter a document title")
        
        # Phase completion
        st.markdown("### Phase Management")
        
        # Check if there are any reports for this phase
        phase_reports = [r for r in st.session_state.reports if r["phase"] == current_phase]
        
        if phase_reports:
            if st.button("Complete Current Phase"):
                complete_current_phase()
                st.success(f"{current_phase_name} phase completed! Moving to next phase.")
                st.experimental_rerun()
        else:
            st.warning("You need to create at least one document before completing this phase.")
    
    with col2:
        # Task Suggestion Agent Section
        st.markdown("### 🧠 Task Suggestion Engine")
        
        # Get task suggestions based on current phase progress
        suggested_tasks = suggest_next_tasks(st.session_state.phase_data)
        
        # Display suggestions in a card
        suggestion_card_html = '<div class="tf-card">'
        suggestion_card_html += '<h4>Suggested Next Tasks</h4>'
        suggestion_card_html += '<ul style="padding-left: 1.5rem;">'
        
        for task in suggested_tasks:
            suggestion_card_html += f'<li style="margin-bottom: 0.75rem;">{task}</li>'
        
        suggestion_card_html += '</ul>'
        
        # Get next phase preview
        next_phase_preview = get_next_phase_preview(st.session_state.phase_data)
        if next_phase_preview:
            suggestion_card_html += f'<div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(124, 77, 255, 0.2);">{next_phase_preview}</div>'
        
        suggestion_card_html += '</div>'
        st.markdown(suggestion_card_html, unsafe_allow_html=True)
        
        st.markdown("### Current Phase Documents")
        
        # Get reports for the current phase
        phase_reports = [r for r in st.session_state.reports if r["phase"] == current_phase]
        
        if phase_reports:
            for report in phase_reports:
                report_card_html = f"""
                <div class="report-card">
                    <h4>{report["title"]}</h4>
                    <p style="font-size: 0.8rem; color: rgba(248, 249, 250, 0.65);">
                        Created: {report["timestamp"].strftime("%Y-%m-%d %H:%M:%S")}
                    </p>
                    <p style="font-size: 0.8rem;">
                        Filename: {report["filename"]}
                    </p>
                </div>
                """
                st.markdown(report_card_html, unsafe_allow_html=True)
        else:
            st.info("No documents created for this phase yet. Use the form to create a new document.")
        
        # Display all phase folders and files
        st.markdown("### All Exported Reports")
        
        if os.path.exists("exports"):
            for phase in phases:
                phase_files = get_phase_files(phase)
                if phase_files:
                    with st.expander(f"{phases[phase]} ({len(phase_files)} files)"):
                        for filename in phase_files:
                            filepath = os.path.join("exports", phase, filename)
                            st.text(filename)
        else:
            st.info("No reports available. The exports directory doesn't exist yet.")

with main_tabs[1]:  # Project Dashboard tab
    # Create a dashboard with key metrics
    st.markdown("## Project Dashboard")
    
    # Display key metrics in a 4-column layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="tf-card" style="text-align: center;">
            <h4 style="margin-bottom: 0.5rem;">Reports Generated</h4>
            <div style="font-size: 2.5rem; font-weight: 700; color: #7c4dff;">
                {reports_count}
            </div>
        </div>
        """.format(reports_count=st.session_state.metrics["reports_generated"]), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="tf-card" style="text-align: center;">
            <h4 style="margin-bottom: 0.5rem;">Phases Completed</h4>
            <div style="font-size: 2.5rem; font-weight: 700; color: #00e676;">
                {phases_count}/6
            </div>
        </div>
        """.format(phases_count=st.session_state.metrics["phases_completed"]), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="tf-card" style="text-align: center;">
            <h4 style="margin-bottom: 0.5rem;">Test Coverage</h4>
            <div style="font-size: 2.5rem; font-weight: 700; color: #ffea00;">
                {coverage}%
            </div>
        </div>
        """.format(coverage=st.session_state.metrics["test_coverage"]), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="tf-card" style="text-align: center;">
            <h4 style="margin-bottom: 0.5rem;">Code Quality</h4>
            <div style="font-size: 2.5rem; font-weight: 700; color: #00e0e0;">
                {quality}%
            </div>
        </div>
        """.format(quality=st.session_state.metrics["code_quality"]), unsafe_allow_html=True)
    
    # Task Suggestion Section in Dashboard
    st.markdown("### 🧠 AI Task Suggestion Engine")
    
    # Create columns for task suggestions
    task_col1, task_col2 = st.columns([3, 2])
    
    with task_col1:
        # Get task suggestions
        suggested_tasks = suggest_next_tasks(st.session_state.phase_data)
        
        suggestion_card_html = '<div class="tf-card">'
        suggestion_card_html += '<h4>Suggested Next Tasks</h4>'
        suggestion_card_html += '<ul style="padding-left: 1.5rem;">'
        
        for task in suggested_tasks:
            suggestion_card_html += f'<li style="margin-bottom: 0.75rem;">{task}</li>'
        
        suggestion_card_html += '</ul>'
        suggestion_card_html += '</div>'
        st.markdown(suggestion_card_html, unsafe_allow_html=True)
    
    with task_col2:
        # Show next phase preview and adaptive guidance
        next_phase_preview = get_next_phase_preview(st.session_state.phase_data)
        
        preview_card_html = '<div class="tf-card">'
        preview_card_html += '<h4>Adaptive Guidance</h4>'
        
        if next_phase_preview:
            preview_card_html += f'<p>{next_phase_preview}</p>'
        
        # Add some general TerraFusion guidance
        preview_card_html += '''
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(124, 77, 255, 0.2);">
            <h5>TerraFusion Framework Tips</h5>
            <ul style="padding-left: 1.5rem;">
                <li>Create documents for each major decision point</li>
                <li>Maintain consistent documentation format</li>
                <li>Use PR generation for code reviews</li>
            </ul>
        </div>
        '''
        
        preview_card_html += '</div>'
        st.markdown(preview_card_html, unsafe_allow_html=True)
    
    # Create visualization of report distribution by phase
    st.markdown("### Report Distribution by Phase")
    
    # Get report statistics
    report_stats = get_report_stats()
    
    # Create dataframe for visualization
    report_df = pd.DataFrame({
        'Phase': list(phases.values()),
        'Reports': [report_stats.get(phase_id, 0) for phase_id in phases.keys()]
    })
    
    # Create a bar chart
    fig = px.bar(
        report_df,
        x='Phase',
        y='Reports',
        color='Reports',
        color_continuous_scale=[[0, "#303030"], [0.5, "#7c4dff"], [1, "#00e676"]],
        height=400
    )
    
    # Customize the layout
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(248,249,250,0.85)'),
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False
    )
    
    # Update bar appearance
    fig.update_traces(
        marker_line_color='rgba(0,0,0,0)',
        marker_line_width=0
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Create a project timeline
    st.markdown("### Project Timeline")
    
    # Create a Gantt chart of phases
    timeline_df = pd.DataFrame({
        'Task': list(phases.values()),
        'Start': [datetime.now() - timedelta(days=i*3) for i in range(len(phases)-1, -1, -1)],
        'Finish': [datetime.now() + timedelta(days=i*3) for i in range(len(phases))],
        'Status': [st.session_state.phase_statuses[phase_id] for phase_id in phases.keys()],
        'Duration': [6 for _ in range(len(phases))]
    })
    
    # Create a color map for the phase statuses
    color_map = {
        'completed': '#00e676',
        'in_progress': '#7c4dff',
        'pending': '#303030'
    }
    
    # Create a Gantt chart
    fig = px.timeline(
        timeline_df, 
        x_start="Start", 
        x_end="Finish", 
        y="Task",
        color="Status",
        color_discrete_map=color_map,
        height=300
    )
    
    # Customize the layout
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(248,249,250,0.85)'),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            autorange="reversed"
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Emergency Override Plan section
    st.markdown("### Emergency Override Plan (EOP)")
    
    with st.expander("Access Emergency Override Plan"):
        st.markdown("""
        <div class="tf-alert warning">
            <h4>Emergency Override Protocol</h4>
            <p>If the AI Agent encounters confusion, risks, or unexpected problems, follow these steps:</p>
            <ol>
                <li>Document the situation in a SITREP (Situation Report)</li>
                <li>Identify assumptions being made and their confidence levels</li>
                <li>Evaluate recovery options and their potential impacts</li>
                <li>Determine the best next action with minimal risk</li>
                <li>If uncertain, pause risky activities until clarification is provided</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Dummy form for emergency override
        with st.form("emergency_override_form"):
            st.text_area("Situation Report (SITREP)", "", placeholder="Describe the current situation and problem...")
            st.text_area("Assumptions", "", placeholder="List assumptions being made and their confidence levels...")
            st.text_area("Recovery Options", "", placeholder="Describe possible recovery paths and their impacts...")
            st.text_area("Recommended Action", "", placeholder="Describe the best next action with minimal risk...")
            
            cols = st.columns([1, 1])
            with cols[0]:
                st.form_submit_button("Submit Emergency Override", type="primary")
            with cols[1]:
                st.form_submit_button("Cancel", type="secondary")

with main_tabs[2]:  # Reports tab
    st.markdown("## Reports Management")
    
    # Provide tools for generating and managing reports
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Report Tools")
        
        st.markdown("""
        <div class="tf-card">
            <h4>Report Organization</h4>
            <p>Use these tools to organize and manage your reports.</p>
        </div>
        """, unsafe_allow_html=True)
        
        run_organize = st.button("Organize Reports")
        if run_organize:
            with st.spinner("Organizing reports..."):
                output = run_script("auto_folder_md_reports.py")
                st.success("Reports organized successfully!")
                st.code(output)
        
        run_generate = st.button("Generate PR Description")
        if run_generate:
            with st.spinner("Generating PR description..."):
                output = run_script("batch_pr_generator.py")
                st.success("PR description generated successfully!")
                if os.path.exists("PR_description.md"):
                    with open("PR_description.md", "r") as f:
                        pr_content = f.read()
                    st.download_button("Download PR Description", pr_content, file_name="PR_description.md")
        
        run_test_reports = st.button("Generate Test Reports")
        if run_test_reports:
            with st.spinner("Generating test reports..."):
                output = run_script("generate_test_reports.py")
                st.success("Test reports generated successfully!")
                st.code(output)
    
    with col2:
        st.markdown("### All Reports")
        
        # Get all report files
        all_files = get_all_report_files()
        
        if all_files:
            # Create a dataframe of all reports
            reports_data = []
            for phase, filename in all_files:
                filepath = os.path.join("exports", phase, filename)
                stat = os.stat(filepath)
                reports_data.append({
                    "Phase": phases.get(phase, phase.capitalize()),
                    "Filename": filename,
                    "Created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                    "Size": f"{stat.st_size / 1024:.1f} KB"
                })
            
            reports_df = pd.DataFrame(reports_data)
            
            # Add filters
            phase_filter = st.multiselect("Filter by Phase", options=reports_df["Phase"].unique())
            
            if phase_filter:
                filtered_df = reports_df[reports_df["Phase"].isin(phase_filter)]
            else:
                filtered_df = reports_df
            
            # Display the dataframe
            st.dataframe(filtered_df, use_container_width=True)
            
            # Allow preview of selected reports
            if not filtered_df.empty:
                selected_report = st.selectbox("Select a report to preview", filtered_df["Filename"])
                if selected_report:
                    selected_phase = filtered_df[filtered_df["Filename"] == selected_report]["Phase"].iloc[0]
                    phase_key = next((k for k, v in phases.items() if v == selected_phase), selected_phase.lower())
                    
                    filepath = os.path.join("exports", phase_key, selected_report)
                    if os.path.exists(filepath):
                        with open(filepath, "r") as f:
                            report_content = f.read()
                        
                        st.markdown("### Report Preview")
                        st.markdown(report_content)
        else:
            st.info("No reports available yet. Create some reports or generate test reports.")

# Check if PR has been generated
if 'pr_generated' in st.session_state and st.session_state.pr_generated:
    st.markdown("### 🎉 Pull Request Description Generated!")
    
    if os.path.exists("PR_description.md"):
        pr_content = ""
        with open("PR_description.md", "r") as f:
            pr_content = f.read()
        
        if pr_content:
            st.markdown(f"""
            <div class="tf-alert success">
                <h4>PR Description Ready for GitHub</h4>
                <p>Your Pull Request description has been generated successfully. You can now copy it to GitHub.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Preview PR Description"):
                st.markdown(pr_content)

# Footer
st.markdown("""
<div style="margin-top: 3rem; text-align: center; color: rgba(248, 249, 250, 0.65); font-size: 0.8rem;">
    🔥 Built with ❤️ using the Immersive CyberSecurity Simulation Framework (ICSF).
    <br>
    Your AI + Human Development Team. Smarter. Faster. Safer.
</div>
""", unsafe_allow_html=True)