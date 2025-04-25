"""
Styling Utilities Module

This module provides functions for loading and applying the TerraFusion UI styling.
"""
import streamlit as st
import os
import base64

def load_css(css_file_path):
    """
    Load and inject CSS from a file into the Streamlit app.
    
    Args:
        css_file_path: Path to the CSS file
    """
    try:
        with open(css_file_path, "r") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            return True
    except Exception as e:
        st.warning(f"Error loading CSS: {e}")
        return False

def apply_terraflow_style():
    """
    Apply the TerraFusion style to the Streamlit app.
    """
    # Load the CSS file
    css_path = os.path.join("styles", "terraflow.css")
    if not load_css(css_path):
        # If the file doesn't exist, use the default CSS
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
            
            /* Card styles */
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
            
            /* Navigation */
            .tf-nav-item {
                display: flex;
                align-items: center;
                padding: 0.5rem 1rem;
                margin-bottom: 0.25rem;
                border-radius: 0.5rem;
                color: var(--tf-text-secondary);
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .tf-nav-item:hover {
                background-color: rgba(0, 229, 255, 0.1);
                color: var(--tf-primary);
            }
            
            .tf-nav-item-active {
                background-color: rgba(0, 229, 255, 0.15);
                color: var(--tf-primary);
                font-weight: 500;
            }
            
            .tf-nav-icon {
                margin-right: 0.5rem;
                display: inline-block;
            }
            
            /* Breadcrumbs */
            .tf-breadcrumb {
                display: flex;
                align-items: center;
                font-size: 0.875rem;
                color: var(--tf-text-tertiary);
                margin-bottom: 1rem;
            }
            
            .tf-breadcrumb-item {
                display: inline-flex;
            }
            
            .tf-breadcrumb-item:not(:last-child)::after {
                content: '/';
                margin: 0 0.25rem;
                color: var(--tf-text-tertiary);
            }
            
            .tf-breadcrumb-item a {
                color: var(--tf-text-secondary);
                text-decoration: none;
            }
            
            .tf-breadcrumb-item a:hover {
                color: var(--tf-primary);
            }
            
            .tf-breadcrumb-active {
                color: var(--tf-primary);
            }
        </style>
        """, unsafe_allow_html=True)

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
    # Use a simple text logo fallback if image is not available
    logo_html = """
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <div style="font-size: 1.5rem; font-weight: 700; color: var(--tf-primary);">
            <span style="color: var(--tf-primary);">Terra</span>
            <span style="color: var(--tf-text);">Fusion</span>
        </div>
    </div>
    """
    
    st.sidebar.markdown(logo_html, unsafe_allow_html=True)