"""
TerraFusion Main Streamlit Application

This is the main entry point for the TerraFusion Streamlit application.
It provides a user interface for accessing various TerraFusion features,
including the Levy Calculator POC that demonstrates Python ↔ Node connectivity.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
from bridge import bridge

# Configure the Streamlit page
st.set_page_config(
    page_title="TerraFusion Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .info-text {
        color: #424242;
        font-size: 1rem;
    }
    .highlight {
        background-color: #f0f7ff;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 3px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown("<h2>TerraFusion Platform</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", [
    "Dashboard", 
    "Levy Calculator POC",
    "Documentation Agent", 
    "Code Analyzer", 
    "Workflow Mapper",
    "API Status"
])

# API status indicator in sidebar
api_status = bridge.get_api_status()
if api_status.get("success", False):
    st.sidebar.success("✅ API Connected")
else:
    st.sidebar.error("❌ API Disconnected")
    st.sidebar.info("Check if the Express server is running")

# Show the selected page
if page == "Dashboard":
    st.markdown("<h1 class='main-header'>TerraFusion Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>An advanced AI-powered code analysis and optimization platform that transforms development workflows through intelligent, interactive multi-agent orchestration.</p>", unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Active Agents", "8", "2 ↑")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Workflow Maps", "3", "1 ↑")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.metric("Optimizations Found", "14", "5 ↑")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("<h2 class='sub-header'>Recent Activity</h2>", unsafe_allow_html=True)
    activity_data = {
        "Timestamp": [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (datetime.now().replace(minute=datetime.now().minute-5)).strftime("%Y-%m-%d %H:%M:%S"),
            (datetime.now().replace(minute=datetime.now().minute-15)).strftime("%Y-%m-%d %H:%M:%S"),
            (datetime.now().replace(minute=datetime.now().minute-30)).strftime("%Y-%m-%d %H:%M:%S"),
        ],
        "Agent": ["Documentation Agent", "Code Analyzer", "Workflow Mapper", "AI Integration Agent"],
        "Action": [
            "Generated API documentation",
            "Completed code analysis",
            "Created workflow visualization",
            "Integrated OpenAI model"
        ]
    }
    st.dataframe(pd.DataFrame(activity_data), use_container_width=True)
    
    # Featured tools
    st.markdown("<h2 class='sub-header'>Featured Tools</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Levy Calculator POC</h3>", unsafe_allow_html=True)
        st.markdown("Demonstrates Python ↔ Node connectivity with a property tax calculator.")
        if st.button("Open Levy Calculator", key="levy_button_1"):
            st.switch_page("Levy Calculator POC")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Workflow Mapper</h3>", unsafe_allow_html=True)
        st.markdown("Visualize and optimize your development workflow patterns.")
        st.button("Coming Soon", disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Levy Calculator POC":
    st.markdown("<h1 class='main-header'>Levy Calculator POC</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>This demo showcases Python ↔ Node connectivity by calculating property tax levy using the Express API server.</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='highlight'>", unsafe_allow_html=True)
    st.markdown("⚙️ **How it works**: When you enter a property ID, the request is sent to the Express API server, which calculates the levy amount and returns the result.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Property ID input
    property_id = st.text_input("Enter Property ID", "123")
    
    if st.button("Calculate Levy"):
        with st.spinner("Calculating..."):
            # Call the API via the bridge
            result = bridge.calculate_property_levy(property_id)
            
            if result.get("success", False):
                levy_data = result.get("data", {})
                
                # Display the result
                st.success(f"Levy calculated successfully!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("<h3>Levy Details</h3>", unsafe_allow_html=True)
                    st.markdown(f"**Property ID:** {levy_data.get('propertyId', 'N/A')}")
                    st.markdown(f"**Tax Year:** {levy_data.get('taxYear', 'N/A')}")
                    st.markdown(f"**Assessment Date:** {levy_data.get('assessmentDate', 'N/A')}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.metric("Levy Amount", f"${levy_data.get('amount', 0):,.2f}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Show raw response for debugging
                with st.expander("View Raw Response"):
                    st.json(result)
            else:
                st.error(f"Failed to calculate levy: {result.get('error', 'Unknown error')}")

elif page == "API Status":
    st.markdown("<h1 class='main-header'>API Status</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>Check the status of the TerraFusion API server and services.</p>", unsafe_allow_html=True)
    
    # Refresh button
    if st.button("Refresh Status"):
        st.experimental_rerun()
    
    # Display API status
    api_status = bridge.get_api_status()
    
    if api_status.get("success", False):
        st.success("✅ API Server is operational")
        
        # Display status details
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>API Details</h3>", unsafe_allow_html=True)
        data = api_status.get("data", {})
        st.markdown(f"**Service:** {data.get('service', 'N/A')}")
        st.markdown(f"**Status:** {data.get('status', 'N/A')}")
        st.markdown(f"**Version:** {data.get('version', 'N/A')}")
        st.markdown(f"**Timestamp:** {data.get('timestamp', 'N/A')}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Show raw response
        with st.expander("View Raw Response"):
            st.json(api_status)
    else:
        st.error("❌ API Server is not responding")
        st.markdown(f"Error: {api_status.get('error', 'Unknown error')}")
        
        st.markdown("<div class='highlight'>", unsafe_allow_html=True)
        st.markdown("**Possible causes:**")
        st.markdown("1. The Express server is not running")
        st.markdown("2. The server is running on a different port or URL")
        st.markdown("3. There's a network connectivity issue")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Troubleshooting tips
        st.markdown("<h3>Troubleshooting</h3>", unsafe_allow_html=True)
        st.markdown("1. Make sure the server is running with `npm run dev` in the server directory")
        st.markdown("2. Check if the API URL is correct: " + bridge.api_url)
        st.markdown("3. Try setting the `TF_API_URL` environment variable if the server is running elsewhere")

else:
    st.markdown(f"<h1 class='main-header'>{page}</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>This feature is coming soon.</p>", unsafe_allow_html=True)
    
    st.info("This functionality will be implemented in an upcoming version of the TerraFusion platform.")
    
    # Back to dashboard button
    if st.button("Back to Dashboard"):
        st.experimental_rerun()  # Will rerun the app, effectively going back to the dashboard