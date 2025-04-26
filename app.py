import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import base64
from datetime import datetime, timedelta
from model_interface import ModelInterface

# Import components
from components.styling import apply_terraflow_style, render_logo
from components.navigation import render_sidebar_navigation, render_page_header
from components.ui_components import (
    render_card, render_metric_card, render_alert, 
    render_info_tooltip, render_progress_bar, render_tag,
    create_gradient_chart
)

# Set page configuration
st.set_page_config(
    page_title="TerraFusion AI Platform",
    page_icon="🌍",
    layout="wide",
)

# Apply consistent styling
apply_terraflow_style()

# Initialize session state
if 'model_interface' not in st.session_state:
    st.session_state.model_interface = ModelInterface()

# Render navigation in sidebar
render_logo()
render_sidebar_navigation()

# Helper functions
def get_random_activity():
    """Generate random activity data for demo purposes"""
    activities = [
        {"time": datetime.now() - timedelta(minutes=5), "type": "analysis", "text": "Code repository analysis completed for TerraFusion Core"},
        {"time": datetime.now() - timedelta(minutes=15), "type": "sync", "text": "Sync operation successful - 245 files processed"},
        {"time": datetime.now() - timedelta(minutes=30), "type": "agent", "text": "Agent 'DatabaseAnalyzer' detected potential optimization"},
        {"time": datetime.now() - timedelta(hours=1), "type": "workflow", "text": "Workflow optimization reduced processing time by 23%"},
        {"time": datetime.now() - timedelta(hours=2), "type": "ai", "text": "AI recommendation implemented for API service layer"},
        {"time": datetime.now() - timedelta(hours=3), "type": "analysis", "text": "Security analysis completed - No vulnerabilities found"},
    ]
    return activities

def get_performance_metrics():
    """Generate performance metrics for demo purposes"""
    return {
        "sync_operations": 127,
        "files_processed": 1463,
        "processing_time": 4.82,
        "optimization_gain": 23
    }

def get_active_alerts():
    """Generate demo alerts"""
    alerts = [
        {"severity": "high", "text": "Cluster performance degradation detected in Node-4", "time": "10 min ago"},
        {"severity": "medium", "text": "Sync service throughput decreased by 15%", "time": "30 min ago"},
        {"severity": "low", "text": "Repository pattern optimization opportunity detected", "time": "2 hours ago"}
    ]
    return alerts

# Header section with breadcrumb and title
render_page_header(
    title="TerraFusion AI Platform",
    subtitle="Advanced AI-powered code analysis and optimization platform"
)

# AI Services Status
st.subheader("AI Service Status")
col1, col2 = st.columns(2)

with col1:
    # Check OpenAI status
    openai_status = st.session_state.model_interface.check_openai_status()
    if openai_status:
        status_text = "**● Connected** - GPT-4o model active\n\nAPI connection established. All advanced code analysis features available."
        render_card("OpenAI Service", status_text, icon="🤖")
    else:
        status_text = "**● Disconnected** - Connection issue\n\nPlease check API key and network connectivity."
        render_alert("OpenAI API connection is not available. Some advanced features may be limited.", level="error")
        render_card("OpenAI Service", status_text, icon="🤖")

with col2:
    # Check Anthropic status
    anthropic_status = st.session_state.model_interface.check_anthropic_status()
    if anthropic_status:
        status_text = "**● Connected** - Claude 3.5 model active\n\nAPI connection established. All specialized reasoning features available."
        render_card("Anthropic Service", status_text, icon="🧠")
    else:
        status_text = "**● Disconnected** - Connection issue\n\nPlease check API key and network connectivity."
        render_alert("Anthropic API connection is not available. Some advanced features may be limited.", level="error")
        render_card("Anthropic Service", status_text, icon="🧠")

# Performance Metrics
st.subheader("System Performance")

metrics = get_performance_metrics()
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card(
        title="Sync Operations",
        value=metrics["sync_operations"],
        unit="operations / day",
        icon="📊",
        trend=5.2  # Example trend showing 5.2% increase
    )

with col2:
    render_metric_card(
        title="Files Processed",
        value=metrics["files_processed"],
        unit="files / day",
        icon="📁",
        trend=12.4  # Example trend showing 12.4% increase
    )

with col3:
    render_metric_card(
        title="Avg. Processing Time",
        value=f"{metrics['processing_time']}",
        unit="sec per file",
        icon="⏱️",
        trend=-8.5  # Example trend showing 8.5% decrease (improvement)
    )

with col4:
    render_metric_card(
        title="Optimization Gain",
        value=metrics["optimization_gain"],
        unit="%",
        icon="🚀",
        trend=3.1  # Example trend showing 3.1% increase
    )

# Add a simple chart for visualization
st.subheader("Processing Performance Trend")
# Create sample data for the chart
data = [10, 8, 6, 7, 5, 4, 4.8, 4.82]  # Processing time trend in seconds
fig = create_gradient_chart(data, title="Processing Time Trend", y_label="Seconds", color="#7c4dff")
st.pyplot(fig)

# Platform Tools Section
st.subheader("Platform Tools")

# First row of features
col1, col2, col3 = st.columns(3)

with col1:
    # Use render_card for consistent styling
    render_card(
        title="Sync Service Dashboard",
        content="Monitor and manage sync operations with real-time metrics, dynamic batch sizing, and performance optimization based on system resources.",
        icon="📊"
    )
    if st.button("Open Sync Service", key="sync"):
        st.switch_page("pages/1_Sync_Service_Dashboard.py")

with col2:
    render_card(
        title="Code Analysis Dashboard",
        content="Analyze code quality, architecture, performance, and security using advanced AI models with actionable recommendations.",
        icon="🔍"
    )
    if st.button("Open Code Analysis", key="code"):
        st.switch_page("pages/2_Code_Analysis_Dashboard.py")

with col3:
    render_card(
        title="Agent Orchestration",
        content="Manage specialized AI agents with different capabilities for enhanced code analysis and continuous optimization.",
        icon="🤖"
    )
    if st.button("Open Agent Orchestration", key="agent"):
        st.switch_page("pages/3_Agent_Orchestration.py")

# Second row of features
col1, col2, col3 = st.columns(3)

with col1:
    render_card(
        title="Workflow Visualization",
        content="Visualize, analyze, and optimize code workflows to identify bottlenecks and improve efficiency with AI-powered insights.",
        icon="🔄"
    )
    if st.button("Open Workflow Visualization", key="workflow"):
        st.switch_page("pages/4_Workflow_Visualization.py")

with col2:
    render_card(
        title="Repository Analysis",
        content="Deep analysis of entire code repositories to evaluate structure, quality, and provide targeted improvement opportunities.",
        icon="📁"
    )
    if st.button("Open Repository Analysis", key="repo"):
        st.switch_page("pages/5_Repository_Analysis.py")

with col3:
    render_card(
        title="AI Chat Interface",
        content="Interactive communication with specialized AI agents to get insights and assistance for development challenges.",
        icon="💬"
    )
    if st.button("Open AI Chat", key="chat"):
        st.switch_page("pages/6_AI_Chat_Interface.py")

# Activity and alerts section
st.subheader("System Activity")
col1, col2 = st.columns([2, 1])

with col1:
    # Prepare activity log for our timeline component
    activities = get_random_activity()
    events = []
    
    for activity in activities:
        time_diff = datetime.now() - activity["time"]
        if time_diff.days > 0:
            time_str = f"{time_diff.days}d ago"
        elif time_diff.seconds // 3600 > 0:
            time_str = f"{time_diff.seconds // 3600}h ago"
        else:
            time_str = f"{time_diff.seconds // 60}m ago"
        
        events.append({
            "time": time_str,
            "title": f"Activity: {activity['type'].title()}",
            "description": activity["text"]
        })
    
    # Use a card with a more descriptive heading
    with st.expander("Recent Activity Log", expanded=True):
        # Create a timeline of events
        for event in events:
            st.markdown(
                f"""
                <div style="display: flex; padding: 0.5rem 0; border-bottom: 1px solid rgba(124, 77, 255, 0.1);">
                    <div style="min-width: 70px; color: rgba(248, 249, 250, 0.65); font-size: 0.875rem;">
                        {event['time']}
                    </div>
                    <div>
                        <div style="font-weight: 500; margin-bottom: 0.25rem; color: #7c4dff;">
                            {event['title']}
                        </div>
                        <div style="color: rgba(248, 249, 250, 0.85); font-size: 0.9rem;">
                            {event['description']}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

with col2:
    # Display active alerts using our alert component
    with st.expander("Active Alerts", expanded=True):
        alerts = get_active_alerts()
        
        if not alerts:
            st.info("No active alerts at this time.")
        else:
            for alert in alerts:
                # Map severity to component's level
                if alert["severity"] == "high":
                    level = "error"
                elif alert["severity"] == "medium":
                    level = "warning"
                else:
                    level = "info"
                
                # Use the alert component
                render_alert(
                    message=f"{alert['text']} ({alert['time']})",
                    level=level,
                    dismissible=True
                )

# Getting started guide
st.subheader("Getting Started")

# Create a cleaner getting started section with progress indicators
col1, col2 = st.columns(2)

with col1:
    render_progress_bar(
        value=1, max_value=4, 
        label="1. Connect AI Services: Configure OpenAI and Anthropic API keys to enable advanced analysis features."
    )
    
    render_progress_bar(
        value=0, max_value=4, 
        label="2. Analyze Your Repository: Get a comprehensive overview of your codebase structure and quality."
    )

with col2:
    render_progress_bar(
        value=0, max_value=4, 
        label="3. Optimize Workflows: Identify and resolve bottlenecks with the Workflow Visualization tool.", 
        style="warning"
    )
    
    render_progress_bar(
        value=0, max_value=4, 
        label="4. Monitor Performance: Track system metrics and optimization with the Sync Service Dashboard."
    )

# Add quick setup help
st.info("👋 **Welcome to TerraFusion AI Platform!** To get started, connect your AI services and explore the platform's capabilities.")

# Add some tags for platform features
st.write("### Platform Features")
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_tag("AI-Powered Analysis", size="medium")
    
with col2:
    render_tag("Multi-Agent System", size="medium")
    
with col3:
    render_tag("Smart Optimization", size="medium")
    
with col4:
    render_tag("2025 Technology", size="medium")

# Footer
st.markdown("""---""")
st.markdown(
    """
    <div style="text-align: center; color: rgba(248, 249, 250, 0.65); font-size: 0.75rem; margin-top: 2rem;">
        © 2025 TerraFusion AI Platform | Advanced Code Analysis and Optimization
    </div>
    """, 
    unsafe_allow_html=True
)