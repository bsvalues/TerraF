"""
Launcher for Code Deep Dive Analyzer

This module serves as the entry point for the application,
providing a way to switch between the original and enhanced versions.
"""
import streamlit as st
import sys
import os

# Set page config
st.set_page_config(
    page_title="Code Deep Dive Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Initialize state
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "original"

def main():
    """Main launcher function"""
    st.title("Code Deep Dive Analyzer Platform")
    
    # App selection
    app_mode = st.sidebar.radio(
        "Select Application Version",
        ["Original", "Enhanced"],
        index=0 if st.session_state.app_mode == "original" else 1
    )
    
    # Update state
    st.session_state.app_mode = app_mode.lower()
    
    # Display selected app
    if st.session_state.app_mode == "original":
        st.sidebar.info("Running original version with base features")
        
        # Import and run original app
        import app
        app.main()
    else:
        st.sidebar.info("Running enhanced version with advanced features")
        st.sidebar.warning("Note: This version requires additional services which may not be available yet")
        
        # Import and run enhanced app
        import enhanced_app
        enhanced_app.main()

if __name__ == "__main__":
    main()