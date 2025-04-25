import streamlit as st
import time
from model_interface import ModelInterface

# Set page configuration
st.set_page_config(
    page_title="TerraFusion AI Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .feature-card {
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        background-color: #f8f9fa;
    }
    .feature-title {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .feature-description {
        font-size: 14px;
        color: #555;
    }
    .api-status-ok {
        color: #4caf50;
        font-weight: bold;
    }
    .api-status-error {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for model interfaces
if 'model_interface' not in st.session_state:
    st.session_state.model_interface = ModelInterface()

# Main content
st.markdown('<div class="main-header">TerraFusion AI Platform</div>', unsafe_allow_html=True)

st.markdown("""
TerraFusion is an advanced AI-powered code analysis and optimization platform that provides intelligent workflow 
management through multi-agent AI orchestration and interactive development insights.

Use the sidebar to navigate between different platform features.
""")

# API Status Section
st.markdown('<div class="sub-header">AI Services Status</div>', unsafe_allow_html=True)

# Check OpenAI API Status
col1, col2 = st.columns(2)

with col1:
    openai_status = st.session_state.model_interface.check_openai_status()
    st.markdown(
        f'<div class="feature-card">'
        f'<div class="feature-title">OpenAI API</div>'
        f'<div class="feature-description">Status: '
        f'<span class="api-status-{"ok" if openai_status else "error"}">'
        f'{"Connected" if openai_status else "Not Connected"}</span></div>'
        f'</div>',
        unsafe_allow_html=True
    )

with col2:
    anthropic_status = st.session_state.model_interface.check_anthropic_status()
    st.markdown(
        f'<div class="feature-card">'
        f'<div class="feature-title">Anthropic API</div>'
        f'<div class="feature-description">Status: '
        f'<span class="api-status-{"ok" if anthropic_status else "error"}">'
        f'{"Connected" if anthropic_status else "Not Connected"}</span></div>'
        f'</div>',
        unsafe_allow_html=True
    )

# Platform Features
st.markdown('<div class="sub-header">Platform Features</div>', unsafe_allow_html=True)

# Feature cards in 3 columns
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-title">Data Synchronization Service</div>'
        '<div class="feature-description">Optimize data synchronization between legacy and modern systems with intelligent, resource-aware batch processing.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Sync Service Dashboard", key="sync_btn"):
        st.switch_page("pages/1_Sync_Service_Dashboard.py")

with col2:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-title">Code Analysis & Optimization</div>'
        '<div class="feature-description">Analyze code quality, architecture, and performance using advanced AI agents.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Code Analysis Dashboard", key="code_btn"):
        st.switch_page("pages/2_Code_Analysis_Dashboard.py")

with col3:
    st.markdown(
        '<div class="feature-card">'
        '<div class="feature-title">Agent Orchestration</div>'
        '<div class="feature-description">Manage and monitor multi-agent AI workflows for complex analysis tasks.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    if st.button("Open Agent Orchestration Dashboard", key="agent_btn"):
        st.switch_page("pages/3_Agent_Orchestration.py")

# Recent Activity
st.markdown('<div class="sub-header">Recent Platform Activity</div>', unsafe_allow_html=True)

# Sample activity log - in real implementation this would come from a database
activity_data = [
    {"timestamp": "2025-04-25 10:15", "activity": "Sync Service full sync completed", "status": "Successful"},
    {"timestamp": "2025-04-25 09:30", "activity": "Code analysis task for repository 'main-api'", "status": "Completed"},
    {"timestamp": "2025-04-25 08:45", "activity": "New agent registered: Database Optimization", "status": "Active"}
]

# Display activity log
st.dataframe(activity_data, use_container_width=True)