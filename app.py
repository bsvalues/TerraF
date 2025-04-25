import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import base64
from datetime import datetime, timedelta
from model_interface import ModelInterface

# Set page configuration
st.set_page_config(
    page_title="TerraFusion AI Platform",
    page_icon="🌍",
    layout="wide",
)

# Define custom CSS to match TerraFusion mockups
st.markdown("""
<style>
    /* TerraFusion color palette and theme */
    :root {
        --tf-primary: #00e5ff;
        --tf-primary-dark: #00b8d4;
        --tf-background: #001529;
        --tf-card-bg: #0a2540;
        --tf-text: #ffffff;
        --tf-text-secondary: rgba(0, 229, 255, 0.7);
        --tf-text-tertiary: rgba(0, 229, 255, 0.5);
        --tf-border: rgba(0, 229, 255, 0.2);
        --tf-success: #00c853;
        --tf-warning: #ffd600;
        --tf-error: #ff1744;
    }
    
    /* Base styles */
    .stApp {
        background-color: var(--tf-background);
    }
    
    /* Header styles */
    .main-header {
        font-size: clamp(2.6rem, 2vw + 1.4rem, 4rem);
        font-weight: 700;
        color: var(--tf-text);
        margin-bottom: 0;
        padding-bottom: 0;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: var(--tf-text-secondary);
        margin-top: 0;
        padding-top: 0;
        margin-bottom: 2rem;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--tf-primary) !important;
        color: var(--tf-background) !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 0.375rem !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
        text-transform: none !important;
        letter-spacing: normal !important;
    }
    
    .stButton > button:hover {
        background-color: var(--tf-primary-dark) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0, 229, 255, 0.3) !important;
    }
    
    /* Section headers */
    h2, h3 {
        color: var(--tf-primary) !important;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1.2rem;
    }
    
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--tf-primary);
        margin-bottom: 1.5rem;
        border-bottom: 1px solid var(--tf-border);
        padding-bottom: 0.5rem;
    }
    
    /* TerraFusion card styles */
    .tf-card {
        background-color: var(--tf-card-bg);
        border: 1px solid var(--tf-border);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.1);
    }
    
    .tf-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background-color: var(--tf-primary);
        opacity: 0.7;
    }
    
    .card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--tf-primary);
        margin-bottom: 1rem;
    }
    
    /* Status indicators */
    .status-online {
        color: var(--tf-success);
        font-weight: 600;
    }
    
    .status-offline {
        color: var(--tf-error);
        font-weight: 600;
    }
    
    /* Dashboard metric card */
    .metric-card {
        background-color: var(--tf-card-bg);
        border: 1px solid var(--tf-border);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        position: relative;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px rgba(0, 229, 255, 0.15);
    }
    
    .metric-title {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--tf-text-secondary);
        margin-bottom: 0.75rem;
    }
    
    .metric-value {
        font-size: clamp(2rem, 1.5vw + 1rem, 3rem);
        font-weight: 700;
        color: var(--tf-text);
        margin-bottom: 0.25rem;
    }
    
    .metric-unit {
        font-size: 0.75rem;
        color: var(--tf-text-tertiary);
        font-weight: 400;
    }
    
    /* Feature card styles */
    .feature-card {
        background-color: var(--tf-card-bg);
        border: 1px solid var(--tf-border);
        border-radius: 0.75rem;
        padding: 1.5rem;
        height: 100%;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px rgba(0, 229, 255, 0.15);
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background-color: var(--tf-primary);
        opacity: 0.7;
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
        color: var(--tf-primary);
    }
    
    .feature-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--tf-primary);
        margin-bottom: 0.75rem;
    }
    
    .feature-description {
        font-size: 0.875rem;
        color: var(--tf-text-tertiary);
        line-height: 1.5;
    }
    
    /* Activity feed */
    .activity-item {
        background-color: var(--tf-card-bg);
        border: 1px solid var(--tf-border);
        border-radius: 0.375rem;
        padding: 1rem;
        margin-bottom: 0.75rem;
        position: relative;
    }
    
    .activity-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
        background-color: var(--tf-primary);
        opacity: 0.7;
    }
    
    .activity-time {
        font-size: 0.75rem;
        color: var(--tf-text-tertiary);
        margin-bottom: 0.5rem;
    }
    
    .activity-content {
        font-size: 0.875rem;
        color: var(--tf-text);
    }
    
    /* Alert styles */
    .alert-item {
        border-radius: 0.375rem;
        padding: 1rem;
        margin-bottom: 0.75rem;
        position: relative;
        background-color: var(--tf-card-bg);
    }
    
    .alert-high::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
        background-color: var(--tf-error);
    }
    
    .alert-medium::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
        background-color: var(--tf-warning);
    }
    
    .alert-low::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
        background-color: var(--tf-success);
    }
    
    /* Glassmorphic container */
    .glassmorphic-container {
        background: rgba(10, 37, 64, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 1rem;
        border: 1px solid var(--tf-border);
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 229, 255, 0.1);
    }
    
    /* Guide section */
    .guide-container {
        background-color: rgba(0, 229, 255, 0.05);
        border: 1px solid var(--tf-border);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-top: 2rem;
    }
    
    .guide-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--tf-primary);
        margin-bottom: 1rem;
    }
    
    .guide-step {
        padding-left: 1rem;
        border-left: 2px solid var(--tf-primary);
        margin-bottom: 1rem;
    }
    
    .guide-step-title {
        font-weight: 600;
        color: var(--tf-text);
        margin-bottom: 0.25rem;
    }
    
    .guide-step-description {
        font-size: 0.875rem;
        color: var(--tf-text-secondary);
    }
    
    /* Footer */
    .footer {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--tf-border);
        text-align: center;
        color: var(--tf-text-tertiary);
        font-size: 0.875rem;
    }
    
    /* TerraFusion watermark/tiny logo */
    .terraform-watermark {
        position: absolute;
        top: 0.75rem;
        right: 0.75rem;
        opacity: 0.1;
        width: 1rem;
        height: 1rem;
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
        {"severity": "high", "text": "Cluster performance degradation detected in Node-4", "time": "10 min ago"},
        {"severity": "medium", "text": "Sync service throughput decreased by 15%", "time": "30 min ago"},
        {"severity": "low", "text": "Repository pattern optimization opportunity detected", "time": "2 hours ago"}
    ]
    return alerts

# Header section with logo
header_container = st.container()
with header_container:
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown('<h1 class="main-header">TerraFusion AI Platform</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Advanced AI-powered code analysis and optimization platform</p>', unsafe_allow_html=True)
    
    # Header separator
    st.markdown('<hr style="border-color: rgba(0, 229, 255, 0.2); margin: 2rem 0;">', unsafe_allow_html=True)

# AI Services Status
st.markdown('<h2 class="section-header">AI Service Status</h2>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="tf-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">OpenAI Service</div>', unsafe_allow_html=True)
    
    # Check OpenAI status
    openai_status = st.session_state.model_interface.check_openai_status()
    if openai_status:
        st.markdown('<span class="status-online">● Connected</span> - GPT-4o model active', unsafe_allow_html=True)
        st.markdown('<p style="color: rgba(0, 229, 255, 0.5); font-size: 0.875rem;">API connection established. All advanced code analysis features available.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-offline">● Disconnected</span> - Connection issue', unsafe_allow_html=True)
        st.markdown('<p style="color: rgba(0, 229, 255, 0.5); font-size: 0.875rem;">Please check API key and network connectivity.</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="tf-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Anthropic Service</div>', unsafe_allow_html=True)
    
    # Check Anthropic status
    anthropic_status = st.session_state.model_interface.check_anthropic_status()
    if anthropic_status:
        st.markdown('<span class="status-online">● Connected</span> - Claude 3.5 model active', unsafe_allow_html=True)
        st.markdown('<p style="color: rgba(0, 229, 255, 0.5); font-size: 0.875rem;">API connection established. All specialized reasoning features available.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-offline">● Disconnected</span> - Connection issue', unsafe_allow_html=True)
        st.markdown('<p style="color: rgba(0, 229, 255, 0.5); font-size: 0.875rem;">Please check API key and network connectivity.</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Performance Metrics
st.markdown('<h2 class="section-header">System Performance</h2>', unsafe_allow_html=True)

metrics = get_performance_metrics()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-title">Sync Operations</div>'
        f'<div class="metric-value">{metrics["sync_operations"]}</div>'
        f'<div class="metric-unit">operations / day</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-title">Files Processed</div>'
        f'<div class="metric-value">{metrics["files_processed"]}</div>'
        f'<div class="metric-unit">files / day</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-title">Avg. Processing Time</div>'
        f'<div class="metric-value">{metrics["processing_time"]}s</div>'
        f'<div class="metric-unit">per file</div>'
        f'</div>',
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-title">Optimization Gain</div>'
        f'<div class="metric-value">{metrics["optimization_gain"]}%</div>'
        f'<div class="metric-unit">performance improvement</div>'
        f'</div>',
        unsafe_allow_html=True
    )

# Platform Tools Section
st.markdown('<h2 class="section-header">Platform Tools</h2>', unsafe_allow_html=True)

# First row of features
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-icon">📊</div>'
        '<div class="feature-title">Sync Service Dashboard</div>'
        '<div class="feature-description">Monitor and manage sync operations with real-time metrics, dynamic batch sizing, and performance optimization based on system resources.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Sync Service", key="sync"):
        st.switch_page("pages/1_Sync_Service_Dashboard.py")

with col2:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-icon">🔍</div>'
        '<div class="feature-title">Code Analysis Dashboard</div>'
        '<div class="feature-description">Analyze code quality, architecture, performance, and security using advanced AI models with actionable recommendations.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Code Analysis", key="code"):
        st.switch_page("pages/2_Code_Analysis_Dashboard.py")

with col3:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-icon">🤖</div>'
        '<div class="feature-title">Agent Orchestration</div>'
        '<div class="feature-description">Manage specialized AI agents with different capabilities for enhanced code analysis and continuous optimization.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Agent Orchestration", key="agent"):
        st.switch_page("pages/3_Agent_Orchestration.py")

# Second row of features
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-icon">🔄</div>'
        '<div class="feature-title">Workflow Visualization</div>'
        '<div class="feature-description">Visualize, analyze, and optimize code workflows to identify bottlenecks and improve efficiency with AI-powered insights.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Workflow Visualization", key="workflow"):
        st.switch_page("pages/4_Workflow_Visualization.py")

with col2:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-icon">📁</div>'
        '<div class="feature-title">Repository Analysis</div>'
        '<div class="feature-description">Deep analysis of entire code repositories to evaluate structure, quality, and provide targeted improvement opportunities.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Repository Analysis", key="repo"):
        st.switch_page("pages/5_Repository_Analysis.py")

with col3:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-icon">💬</div>'
        '<div class="feature-title">AI Chat Interface</div>'
        '<div class="feature-description">Interactive communication with specialized AI agents to get insights and assistance for development challenges.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open AI Chat", key="chat"):
        st.switch_page("pages/6_AI_Chat_Interface.py")

# Activity and alerts section
st.markdown('<h2 class="section-header">System Activity</h2>', unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="glassmorphic-container">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Recent Activity</div>', unsafe_allow_html=True)
    
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
            f'<div class="activity-item">'
            f'<div class="activity-time">{time_str}</div>'
            f'<div class="activity-content">{activity["text"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glassmorphic-container">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Active Alerts</div>', unsafe_allow_html=True)
    
    alerts = get_active_alerts()
    
    if not alerts:
        st.markdown('<p style="color: var(--tf-text-tertiary); font-size: 0.875rem;">No active alerts</p>', unsafe_allow_html=True)
    else:
        for alert in alerts:
            severity_class = f"alert-{alert['severity']}"
            st.markdown(
                f'<div class="alert-item {severity_class}">'
                f'<div class="activity-time">{alert["time"]}</div>'
                f'<div class="activity-content">{alert["text"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Getting started guide
st.markdown('<div class="guide-container">', unsafe_allow_html=True)
st.markdown('<div class="guide-title">Getting Started</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="guide-step">'
    '<div class="guide-step-title">1. Connect AI Services</div>'
    '<div class="guide-step-description">Configure your OpenAI and Anthropic API keys to enable advanced analysis features.</div>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="guide-step">'
    '<div class="guide-step-title">2. Analyze Your Repository</div>'
    '<div class="guide-step-description">Use the Repository Analysis tool to get a comprehensive overview of your codebase.</div>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="guide-step">'
    '<div class="guide-step-title">3. Optimize Workflows</div>'
    '<div class="guide-step-description">Identify and resolve bottlenecks with the Workflow Visualization tool.</div>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="guide-step">'
    '<div class="guide-step-title">4. Monitor Performance</div>'
    '<div class="guide-step-description">Track system metrics and optimization with the Sync Service Dashboard.</div>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("© 2025 TerraFusion AI Platform | Advanced Code Analysis and Optimization", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)