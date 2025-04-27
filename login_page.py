"""
TerraFusion Platform Login Page

This module provides a Streamlit login page for the TerraFusion platform.
"""

import streamlit as st
from auth_manager import authenticate, validate_session

def display_login_page():
    """
    Display the login page and handle authentication.
    
    Returns:
        True if user is authenticated, False otherwise
    """
    # Check if user is already authenticated
    if "auth_token" in st.session_state and validate_session(st.session_state["auth_token"]):
        return True
    
    # Set page title and header
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 2rem;">
        <div style="font-size: 2.5rem; margin-right: 1rem;">🚀</div>
        <div>
            <h1 style="margin: 0; background: linear-gradient(90deg, #7c4dff, #00e0e0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem;">TerraFusion Platform</h1>
            <p style="margin: 0; font-size: 1.2rem; opacity: 0.8;">AI-Driven Code Analysis & DevOps Framework</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create login form
    with st.form("login_form"):
        st.markdown("<h2>🔐 Authentication</h2>", unsafe_allow_html=True)
        
        # Username input
        username = st.text_input("Username", key="username_input")
        
        # Password input
        password = st.text_input("Password", type="password", key="password_input")
        
        # Login button
        submit_button = st.form_submit_button("Login")
        
        # Handle login attempt
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password.")
                return False
            
            # Attempt authentication
            auth_token = authenticate(username, password)
            if auth_token:
                # Store auth token in session
                st.session_state["auth_token"] = auth_token
                st.session_state["username"] = username
                
                # Rerun the app to show the main interface
                st.rerun()
                return True
            else:
                st.error("Invalid username or password.")
                return False
    
    # Default login information for first-time users
    st.markdown("""
    <div style="margin-top: 2rem; padding: 1rem; border: 1px solid rgba(124, 77, 255, 0.25); border-radius: 0.5rem; background-color: rgba(124, 77, 255, 0.05);">
        <h3 style="margin-top: 0;">👤 Default Login</h3>
        <p>For first-time access, use the following credentials:</p>
        <ul>
            <li><strong>Username:</strong> admin</li>
            <li><strong>Password:</strong> terrafusion</li>
        </ul>
        <p style="margin-bottom: 0; font-style: italic;">Note: Please change the default password after your first login.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show platform features section
    st.markdown("""
    <div style="margin-top: 2rem;">
        <h2>🚀 Platform Features</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem;">
            <div style="background-color: #1e1e1e; border-radius: 0.5rem; padding: 1.5rem; border: 1px solid rgba(124, 77, 255, 0.25);">
                <h3 style="margin-top: 0;">📊 Phase Tracking</h3>
                <p>Monitor project phases with visual progress indicators.</p>
            </div>
            <div style="background-color: #1e1e1e; border-radius: 0.5rem; padding: 1.5rem; border: 1px solid rgba(124, 77, 255, 0.25);">
                <h3 style="margin-top: 0;">🧠 AI Task Suggestions</h3>
                <p>Get intelligent task recommendations based on your project's current phase.</p>
            </div>
            <div style="background-color: #1e1e1e; border-radius: 0.5rem; padding: 1.5rem; border: 1px solid rgba(124, 77, 255, 0.25);">
                <h3 style="margin-top: 0;">📝 Documentation Generation</h3>
                <p>Automatically generate and manage project documentation.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return False