import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import time
import os
from datetime import datetime, timedelta
from model_interface import ModelInterface

# Set page configuration
st.set_page_config(
    page_title="TerraFusion AI Platform",
    page_icon="🧠",
    layout="wide",
)

# Define custom CSS
st.markdown("""
<style>
    /* TerraFusion color palette */
    :root {
        --tf-primary: #2E7D32;
        --tf-primary-light: #4CAF50;
        --tf-primary-dark: #1B5E20;
        --tf-secondary: #3949AB;
        --tf-secondary-light: #5C6BC0;
        --tf-accent: #FF6F00;
        --tf-background: #F5F7FA;
        --tf-card: #FFFFFF;
        --tf-text: #263238;
        --tf-text-light: #78909C;
        --tf-success: #00C853;
        --tf-warning: #FFD600;
        --tf-error: #D50000;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--tf-background);
    }
    
    /* Header styles */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: var(--tf-primary-dark);
        margin-bottom: 0;
        padding-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: var(--tf-text-light);
        margin-top: 0;
        padding-top: 0;
        margin-bottom: 2rem;
    }
    
    /* Status card styles */
    .status-card {
        padding: 20px;
        border-radius: 12px;
        background-color: var(--tf-card);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 24px;
        border-top: 4px solid var(--tf-primary);
    }
    .status-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--tf-primary-dark);
        margin-bottom: 12px;
    }
    .status-online {
        color: var(--tf-success);
        font-weight: 600;
    }
    .status-offline {
        color: var(--tf-error);
        font-weight: 600;
    }
    
    /* Feature card styles */
    .feature-card {
        border-radius: 12px;
        background-color: var(--tf-card);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        height: 100%;
        border-left: 4px solid var(--tf-primary);
    }
    .feature-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
    }
    .feature-content {
        padding: 24px;
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 16px;
        color: var(--tf-primary);
    }
    .feature-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--tf-primary-dark);
        margin-bottom: 12px;
    }
    .feature-description {
        font-size: 1rem;
        color: var(--tf-text-light);
        line-height: 1.5;
    }
    
    /* Activity & alert card styles */
    .activity-card {
        padding: 16px;
        border-radius: 8px;
        background-color: var(--tf-card);
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border-left: 3px solid var(--tf-secondary);
    }
    .activity-time {
        font-size: 0.85rem;
        color: var(--tf-text-light);
        margin-bottom: 4px;
    }
    .activity-text {
        font-size: 1rem;
        color: var(--tf-text);
    }
    
    /* Metric box styles */
    .metric-box {
        border-radius: 12px;
        padding: 20px;
        background-color: var(--tf-card);
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        height: 100%;
        border-top: 4px solid var(--tf-primary-light);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--tf-primary-dark);
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1rem;
        color: var(--tf-text-light);
        font-weight: 500;
    }
    
    /* Alert styles */
    .alert-card {
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        background-color: var(--tf-card);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .alert-high {
        border-left: 3px solid var(--tf-error);
    }
    .alert-medium {
        border-left: 3px solid var(--tf-warning);
    }
    .alert-low {
        border-left: 3px solid var(--tf-success);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--tf-primary);
        color: white;
        font-weight: 500;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: var(--tf-primary-dark);
        color: white;
    }
    
    /* Section headers */
    h2 {
        color: var(--tf-primary-dark);
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--tf-primary-light);
    }
    
    /* Footer */
    .footer {
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #ECEFF1;
        text-align: center;
        color: var(--tf-text-light);
        font-size: 0.9rem;
    }
    
    /* Navigation improvements */
    .nav-section {
        margin-top: 30px;
        margin-bottom: 40px;
    }
    .nav-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--tf-primary-dark);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'model_interface' not in st.session_state:
    st.session_state.model_interface = ModelInterface()

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
        {"severity": "medium", "text": "Sync service throughput decreased by 15%", "time": "30 min ago"},
        {"severity": "low", "text": "Repository pattern optimization opportunity detected", "time": "2 hours ago"}
    ]
    return alerts

# Main dashboard header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h1 class="main-header">TerraFusion AI Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Advanced AI-powered code analysis and optimization platform</p>', unsafe_allow_html=True)

# AI Services Status
st.subheader("AI Services Status")
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.markdown('<div class="status-header">OpenAI Service</div>', unsafe_allow_html=True)
    
    # Check OpenAI status
    openai_status = st.session_state.model_interface.check_openai_status()
    if openai_status:
        st.markdown('<span class="status-online">● Online</span> - GPT-4o model ready', unsafe_allow_html=True)
        st.markdown('API connection established and verified. Full functionality available.', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-offline">● Offline</span> - Connection issue', unsafe_allow_html=True)
        st.markdown('Please check API key and network connectivity.', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.markdown('<div class="status-header">Anthropic Service</div>', unsafe_allow_html=True)
    
    # Check Anthropic status
    anthropic_status = st.session_state.model_interface.check_anthropic_status()
    if anthropic_status:
        st.markdown('<span class="status-online">● Online</span> - Claude 3 model ready', unsafe_allow_html=True)
        st.markdown('API connection established and verified. Full functionality available.', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-offline">● Offline</span> - Connection issue', unsafe_allow_html=True)
        st.markdown('Please check API key and network connectivity.', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Performance Metrics
st.subheader("System Performance")

metrics = get_performance_metrics()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f'<div class="metric-box">'
        f'<div class="metric-value">{metrics["sync_operations"]}</div>'
        f'<div class="metric-label">Sync Operations</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f'<div class="metric-box">'
        f'<div class="metric-value">{metrics["files_processed"]}</div>'
        f'<div class="metric-label">Files Processed</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f'<div class="metric-box">'
        f'<div class="metric-value">{metrics["processing_time"]}s</div>'
        f'<div class="metric-label">Avg. Processing Time</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f'<div class="metric-box">'
        f'<div class="metric-value">{metrics["optimization_gain"]}%</div>'
        f'<div class="metric-label">Optimization Gain</div>'
        f'</div>',
        unsafe_allow_html=True
    )

# Features Section
st.subheader("Platform Tools")

# First row of features
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-content">'
        '<div class="feature-icon">📊</div>'
        '<div class="feature-title">Sync Service Dashboard</div>'
        '<div class="feature-description">Monitor and manage sync operations with real-time metrics, dynamic batch sizing, and performance optimization.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Sync Service", key="sync"):
        st.switch_page("pages/1_Sync_Service_Dashboard.py")

with col2:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-content">'
        '<div class="feature-icon">🔍</div>'
        '<div class="feature-title">Code Analysis Dashboard</div>'
        '<div class="feature-description">Analyze code quality, architecture, performance, and security using advanced AI models.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Code Analysis", key="code"):
        st.switch_page("pages/2_Code_Analysis_Dashboard.py")

with col3:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-content">'
        '<div class="feature-icon">🤖</div>'
        '<div class="feature-title">Agent Orchestration</div>'
        '<div class="feature-description">Manage specialized AI agents with different capabilities for enhanced code analysis and optimization.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Agent Orchestration", key="agent"):
        st.switch_page("pages/3_Agent_Orchestration.py")

st.markdown("<br>", unsafe_allow_html=True)

# Second row of features
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-content">'
        '<div class="feature-icon">🔄</div>'
        '<div class="feature-title">Workflow Visualization</div>'
        '<div class="feature-description">Visualize, analyze, and optimize code workflows to identify bottlenecks and improve efficiency.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Workflow Visualization", key="workflow"):
        st.switch_page("pages/4_Workflow_Visualization.py")

with col2:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-content">'
        '<div class="feature-icon">📁</div>'
        '<div class="feature-title">Repository Analysis</div>'
        '<div class="feature-description">Deep analysis of entire code repositories to evaluate structure, quality, and improvement opportunities.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Repository Analysis", key="repo"):
        st.switch_page("pages/5_Repository_Analysis.py")

with col3:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-content">'
        '<div class="feature-icon">💬</div>'
        '<div class="feature-title">AI Chat Interface</div>'
        '<div class="feature-description">Interactive communication with specialized AI agents to get insights and assistance for development.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open AI Chat", key="chat"):
        st.switch_page("pages/6_AI_Chat_Interface.py")

# System Activity and Alerts
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Recent Activity")
    activities = get_random_activity()
    
    for activity in activities:
        time_diff = datetime.now() - activity["time"]
        if time_diff.days > 0:
            time_str = f"{time_diff.days}d ago"
        elif time_diff.seconds // 3600 > 0:
            time_str = f"{time_diff.seconds // 3600}h ago"
        else:
            time_str = f"{time_diff.seconds // 60}m ago"
        
        st.markdown(
            f'<div class="activity-card">'
            f'<div class="activity-time">{time_str}</div>'
            f'<div class="activity-text">{activity["text"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

with col2:
    st.subheader("Active Alerts")
    alerts = get_active_alerts()
    
    if not alerts:
        st.info("No active alerts")
    else:
        for alert in alerts:
            severity_class = f"alert-{alert['severity']}"
            st.markdown(
                f'<div class="alert-card {severity_class}">'
                f'<div class="activity-time">{alert["time"]}</div>'
                f'<div class="activity-text">{alert["text"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

# Quick Start Guide
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("Quick Start Guide")

with st.expander("Getting Started with TerraFusion AI Platform", expanded=False):
    st.markdown("""
    ### First Steps with TerraFusion AI Platform
    
    1. **Connect AI Services** - Ensure your OpenAI and/or Anthropic API keys are configured
    2. **Analyze a Repository** - Use the Repository Analysis tool to evaluate your codebase
    3. **Optimize Workflows** - Identify and fix bottlenecks with the Workflow Visualization
    4. **Monitor Performance** - Track system performance with the Sync Service Dashboard
    
    ### Key Features
    
    - **Multi-Model AI Analysis** - Leverage both OpenAI and Anthropic models for comprehensive code insights
    - **Adaptive Performance** - Dynamic batch sizing automatically adjusts based on system resources
    - **Specialized Agents** - Domain-specific AI agents focus on different aspects of your codebase
    - **Interactive Visualizations** - Visual representations of code workflows and architecture
    """)

# Footer
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("© 2025 TerraFusion AI Platform | Advanced Code Analysis and Optimization", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)