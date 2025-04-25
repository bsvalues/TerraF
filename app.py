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
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #888;
        margin-top: 0;
    }
    .status-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .status-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .status-online {
        color: #4CAF50;
        font-weight: bold;
    }
    .status-offline {
        color: #F44336;
        font-weight: bold;
    }
    .feature-card {
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
        height: 100%;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .feature-content {
        padding: 20px;
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 10px;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .feature-description {
        font-size: 0.9rem;
        color: #555;
    }
    .activity-card {
        padding: 10px 15px;
        border-radius: 8px;
        background-color: #f0f0f0;
        margin-bottom: 10px;
    }
    .activity-time {
        font-size: 0.8rem;
        color: #666;
    }
    .activity-text {
        font-size: 0.9rem;
    }
    .metric-box {
        border-radius: 8px;
        padding: 15px;
        background-color: #f0f0f0;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #555;
    }
    .alert-card {
        padding: 10px 15px;
        border-radius: 8px;
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
        margin-bottom: 10px;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .alert-medium {
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
    }
    .alert-low {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
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

# Main dashboard
st.markdown('<h1 class="main-header">TerraFusion AI Platform</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced AI-powered code analysis and optimization platform</p>', unsafe_allow_html=True)

# AI Services Status
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
st.subheader("Platform Features")

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

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("© 2025 TerraFusion AI Platform | Advanced Code Analysis and Optimization", unsafe_allow_html=True)