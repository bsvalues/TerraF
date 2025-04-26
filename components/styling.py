"""
Styling Utilities Module

This module provides functions for loading and applying the TerraFusion UI styling.
"""
import streamlit as st
import os
import base64

def apply_terraflow_style():
    """
    Apply the TerraFusion style to the Streamlit app.
    """
    # Apply basic styling that works reliably
    st.markdown(
        """
        <style>
        /* Modern dark theme with cyberpunk accents */
        :root {
            --tf-primary: #7c4dff;
            --tf-primary-light: #b47cff;
            --tf-primary-dark: #3f1dcb;
            --tf-accent: #00e0e0;
            --tf-accent-light: #73ffff;
            --tf-accent-dark: #00b0b0;
            --tf-background: #121212;
            --tf-card-bg: #1e1e1e;
            --tf-text: #f8f9fa;
            --tf-text-secondary: rgba(248, 249, 250, 0.85);
            --tf-text-tertiary: rgba(248, 249, 250, 0.65);
            --tf-border: rgba(124, 77, 255, 0.25);
            --tf-border-light: rgba(124, 77, 255, 0.1);
            --tf-success: #00e676;
            --tf-warning: #ffea00;
            --tf-error: #ff1744;
        }
        
        /* Base styles */
        .stApp {
            background-color: var(--tf-background);
            color: var(--tf-text);
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: var(--tf-primary);
            font-weight: 600;
            margin-bottom: 1rem;
            line-height: 1.2;
        }
        
        h1 {
            font-size: 2.5rem;
            color: var(--tf-text);
        }
        
        h2 {
            font-size: 2rem;
            color: var(--tf-text);
            position: relative;
            margin-bottom: 1.5rem;
        }
        
        h3 {
            font-size: 1.5rem;
        }
        
        p {
            margin-bottom: 1rem;
            font-size: 1rem;
            line-height: 1.6;
        }
        
        /* Button styles */
        .stButton > button {
            background-color: var(--tf-primary) !important;
            color: white !important;
            font-weight: 500 !important;
            border: none !important;
            padding: 0.6rem 1.25rem !important;
            border-radius: 0.375rem !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            width: 100% !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Cards and containers */
        .tf-card {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            position: relative;
        }
        
        /* Header for pages */
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--tf-primary);
            margin-bottom: 0;
            padding-bottom: 0;
        }
        
        .sub-header {
            font-size: 1.2rem;
            color: var(--tf-text-secondary);
            margin-top: 0.5rem;
            margin-bottom: 2rem;
        }
        
        /* Card title styling */
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--tf-primary);
            margin-bottom: 1rem;
        }

        /* Feature card styling */
        .feature-card {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            height: 100%;
            display: flex;
            flex-direction: column;
        }

        .feature-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            color: var(--tf-primary);
        }

        .feature-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--tf-primary);
        }

        .feature-description {
            color: var(--tf-text-secondary);
            font-size: 0.875rem;
            flex-grow: 1;
        }

        /* Section headers */
        .section-header {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 2rem 0 1rem 0;
            color: var(--tf-primary);
            position: relative;
            display: inline-block;
        }

        /* Metrics cards */
        .metric-card {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: 0.75rem;
            padding: 1rem;
            text-align: center;
            height: 100%;
        }

        .metric-title {
            color: var(--tf-text-secondary);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--tf-primary);
            margin-bottom: 0.25rem;
        }

        .metric-unit {
            font-size: 0.75rem;
            color: var(--tf-text-tertiary);
        }

        /* Activity feed */
        .glassmorphic-container {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .activity-item {
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--tf-border-light);
            display: flex;
            align-items: flex-start;
        }

        .activity-time {
            color: var(--tf-text-tertiary);
            font-size: 0.75rem;
            min-width: 50px;
            margin-right: 1rem;
        }

        .activity-content {
            color: var(--tf-text-secondary);
            font-size: 0.875rem;
            flex-grow: 1;
        }

        /* Alerts */
        .alert-item {
            padding: 0.75rem;
            border-radius: 0.5rem;
            margin-bottom: 0.75rem;
            background-color: rgba(30, 30, 30, 0.5);
            border-left: 3px solid var(--tf-primary);
        }

        .alert-high {
            border-left-color: var(--tf-error);
        }

        .alert-medium {
            border-left-color: var(--tf-warning);
        }

        .alert-low {
            border-left-color: var(--tf-success);
        }

        /* Status indicators */
        .status-online {
            color: var(--tf-success);
        }

        .status-offline {
            color: var(--tf-error);
        }

        /* Guide section */
        .guide-container {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }

        .guide-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--tf-primary);
            margin-bottom: 1rem;
        }

        .guide-step {
            margin-bottom: 1rem;
            padding-left: 1rem;
            border-left: 2px solid var(--tf-border);
            position: relative;
        }

        .guide-step-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: var(--tf-text);
        }

        .guide-step-description {
            font-size: 0.875rem;
            color: var(--tf-text-secondary);
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem 0 1rem 0;
            color: var(--tf-text-tertiary);
            font-size: 0.75rem;
            margin-top: 3rem;
            border-top: 1px solid var(--tf-border-light);
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

def get_image_base64(img_path):
    """
    Get the base64 encoded string of an image.
    
    Args:
        img_path: Path to the image file
        
    Returns:
        str: Base64 encoded string of the image
    """
    try:
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.warning(f"Error loading image: {e}")
        return None

def render_logo():
    """
    Render the TerraFusion logo.
    """
    # Simple logo that works reliably
    logo_html = """
    <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(124, 77, 255, 0.1);">
        <div style="font-size: 1.5rem; font-weight: 700; color: #7c4dff;">
            TerraFusion AI
        </div>
    </div>
    """
    
    st.sidebar.markdown(logo_html, unsafe_allow_html=True)