"""
TerraFusion Levy Calculator POC

This Streamlit app demonstrates the Python-to-Node connectivity
by calculating property levies using the TerraFusion API.
"""

import streamlit as st
from datetime import datetime
import sys
import os
import json
import requests

# Add the project root to the path to import the bridge module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from bridge import get_bridge

# Configure the bridge with the API URL
bridge = get_bridge("http://localhost:4000")

# Configure the Streamlit page
st.set_page_config(
    page_title="TerraFusion Levy Calculator POC",
    page_icon="🏠",
    layout="centered",
)

# Apply custom styling
st.markdown("""
<style>
    .header {
        font-size: 2rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .highlight {
        background-color: #f0f7ff;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 3px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Main app
st.markdown("<h1 class='header'>Levy Calculator POC</h1>", unsafe_allow_html=True)
st.markdown("This demonstration showcases the Python-to-Node connectivity by calculating property tax levies.")

# Check API connection
api_status = bridge.get_api_status()
if api_status.get("success", False):
    st.success("✅ API Connected")
else:
    st.error("❌ API Disconnected")
    st.info("Please make sure the Express server is running.")
    st.stop()

# Property ID input
st.markdown("<div class='highlight'>", unsafe_allow_html=True)
st.markdown("⚙️ **How it works**: Enter a property ID and click 'Calculate Levy'. The request is sent to the Express API server, which calculates the levy amount and returns the result.")
st.markdown("</div>", unsafe_allow_html=True)

property_id = st.text_input("Enter Property ID", "123")

if st.button("Calculate Levy"):
    with st.spinner("Calculating property levy..."):
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

# Show technical information
with st.expander("Technical Details"):
    st.markdown("### Python-to-Node Connectivity")
    st.markdown("""
    This POC demonstrates the seamless integration between the Python-based Streamlit 
    application and the Node.js Express API server. The bridge module handles the 
    communication between the two environments.
    
    **Components:**
    - Python Streamlit frontend (this app)
    - TerraFusionBridge module for Python-to-Node communication
    - Express API server with levy calculation endpoint
    """)
    
    st.markdown("### API Information")
    st.markdown(f"**API URL:** {bridge.api_url}")
    st.markdown(f"**Endpoints Used:**")
    st.markdown(f"- `/api/status` - Check API server status")
    st.markdown(f"- `/api/v1/levy?propertyId=123` - Calculate property levy")

# Footer
st.markdown("---")
st.markdown("<small>TerraFusion Platform &copy; 2025</small>", unsafe_allow_html=True)