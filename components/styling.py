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
    # Use our cyberpunk styling directly instead of loading from file to ensure it works
    st.markdown(
        """
        <style>
        /* Base color palette - modern cyberpunk/tech theme */
        :root {
            --tf-primary: #6200ea;
            --tf-primary-light: #9d46ff;
            --tf-primary-dark: #0a00b6;
            --tf-accent: #00e5ff;
            --tf-accent-light: #73ffff;
            --tf-accent-dark: #00b8d4;
            --tf-background: #121212;
            --tf-card-bg: #1e1e1e;
            --tf-card-bg-hover: #252525;
            --tf-text: #ffffff;
            --tf-text-secondary: rgba(255, 255, 255, 0.85);
            --tf-text-tertiary: rgba(255, 255, 255, 0.65);
            --tf-border: rgba(98, 0, 234, 0.3);
            --tf-border-light: rgba(98, 0, 234, 0.15);
            --tf-success: #00e676;
            --tf-warning: #ffea00;
            --tf-error: #ff1744;
            --tf-shadow: rgba(0, 0, 0, 0.5);
            --tf-glow: rgba(98, 0, 234, 0.4);
        }
        
        /* Base styles */
        .stApp {
            background-color: var(--tf-background);
            color: var(--tf-text);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            position: relative;
        }
        
        /* Add futuristic elements */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(98, 0, 234, 0.03) 0%, transparent 20%),
                radial-gradient(circle at 90% 80%, rgba(0, 229, 255, 0.03) 0%, transparent 20%),
                linear-gradient(135deg, rgba(10, 0, 182, 0.01) 0%, rgba(98, 0, 234, 0.02) 100%);
            pointer-events: none;
            z-index: -1;
        }
        
        /* Glowing accent line at the top */
        .stApp::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--tf-accent-dark), var(--tf-primary), var(--tf-accent), var(--tf-primary-dark));
            z-index: 1000;
            box-shadow: 0 0 10px var(--tf-glow), 0 0 20px var(--tf-glow), 0 0 30px var(--tf-glow);
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
        }
        
        h2 {
            font-size: 2rem;
        }
        
        h3 {
            font-size: 1.5rem;
        }
        
        /* Header styles - cyberpunk inspired */
        .tf-header-container {
            position: relative;
            margin-bottom: 1rem;
        }
        
        .tf-page-title {
            font-size: clamp(1.8rem, 2vw + 1rem, 2.5rem);
            font-weight: 700;
            color: white;
            margin: 0;
            padding: 0;
            position: relative;
            display: inline-block;
            background: linear-gradient(90deg, white, var(--tf-primary-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 0.5px;
            text-shadow: 0 0 10px var(--tf-glow);
        }
        
        .tf-title-accent {
            position: absolute;
            bottom: -8px;
            left: 0;
            height: 3px;
            width: 60px;
            background: linear-gradient(90deg, var(--tf-primary), var(--tf-accent));
            box-shadow: 0 0 10px var(--tf-glow);
        }
        
        .tf-subtitle {
            font-size: 1rem;
            color: var(--tf-text-secondary);
            margin: 0.25rem 0 1.5rem 0;
            font-weight: 400;
            letter-spacing: 0.3px;
            opacity: 0.85;
            max-width: 800px;
        }
        
        /* Breadcrumb */
        .tf-breadcrumb {
            display: flex;
            align-items: center;
            font-size: 0.875rem;
            color: var(--tf-text-tertiary);
            margin-bottom: 1rem;
        }
        
        .tf-breadcrumb-item:not(:last-child)::after {
            content: '/';
            margin: 0 0.25rem;
            color: var(--tf-text-tertiary);
        }
        
        .tf-breadcrumb-item a {
            color: var(--tf-text-secondary);
            text-decoration: none;
            transition: color 0.15s ease;
        }
        
        .tf-breadcrumb-item a:hover {
            color: var(--tf-primary);
        }
        
        .tf-breadcrumb-active {
            color: var(--tf-primary);
        }
        
        /* Card component - with futuristic elements */
        .tf-card {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 12px var(--tf-shadow);
            transition: all 0.25s ease;
        }
        
        /* Futuristic edge accent */
        .tf-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(to bottom, var(--tf-primary), var(--tf-accent));
            opacity: 0.8;
        }
        
        /* Button styles - futuristic/cyberpunk design */
        .tf-button, .stButton > button {
            background-color: var(--tf-primary) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 0.5rem 1.5rem !important;
            border-radius: 2px !important;
            cursor: pointer !important;
            transition: all 0.15s ease !important;
            text-align: center !important;
            display: inline-block !important;
            position: relative !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            font-size: 0.9rem !important;
            overflow: hidden !important;
            box-shadow: 0 4px 12px rgba(98, 0, 234, 0.3) !important;
            z-index: 1 !important;
            width: 100% !important;
        }
        
        .tf-button:hover, .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 24px rgba(98, 0, 234, 0.4), 0 0 10px var(--tf-glow) !important;
            color: white !important;
        }
        
        /* Navigation - cyberpunk style */
        .tf-nav-item {
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            color: var(--tf-text-secondary);
            text-decoration: none;
            border-radius: 2px;
            transition: all 0.15s ease;
            margin-bottom: 0.5rem;
            position: relative;
            overflow: hidden;
            border-left: 2px solid transparent;
        }
        
        .tf-nav-item:hover {
            background-color: rgba(98, 0, 234, 0.1);
            color: var(--tf-primary-light);
            border-left-color: var(--tf-primary-light);
            padding-left: calc(1rem + 4px);
        }
        
        .tf-nav-item-active {
            background-color: rgba(98, 0, 234, 0.15);
            color: var(--tf-primary);
            font-weight: 500;
            border-left: 2px solid var(--tf-primary);
            padding-left: calc(1rem + 4px);
            box-shadow: 0 0 10px rgba(98, 0, 234, 0.2);
        }
        
        .tf-nav-icon {
            margin-right: 0.5rem;
            font-size: 1.2em;
            transition: transform 0.15s ease;
        }
        
        .tf-nav-item:hover .tf-nav-icon {
            transform: translateX(3px);
        }
        
        /* Sidebar header styling */
        .tf-sidebar-header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--tf-border-light);
        }
        
        .tf-sidebar-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--tf-primary);
            margin: 0;
            background: linear-gradient(90deg, var(--tf-primary), var(--tf-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* Badges */
        .tf-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .tf-badge-success {
            background-color: rgba(0, 200, 83, 0.15);
            color: var(--tf-success);
        }
        
        .tf-badge-warning {
            background-color: rgba(255, 214, 0, 0.15);
            color: var(--tf-warning);
        }
        
        .tf-badge-error {
            background-color: rgba(255, 23, 68, 0.15);
            color: var(--tf-error);
        }

        /* Legacy class support */
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

        /* Additional UI components */
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--tf-primary);
            margin-bottom: 1rem;
        }

        .feature-card {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
        }

        .feature-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, var(--tf-primary), var(--tf-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
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

        .section-header {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 2rem 0 1rem 0;
            color: var(--tf-primary);
            position: relative;
            display: inline-block;
        }

        .section-header::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 50px;
            height: 2px;
            background: linear-gradient(90deg, var(--tf-primary), var(--tf-accent));
        }

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

        .glassmorphic-container {
            background: rgba(30, 30, 30, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
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

        .status-online {
            color: var(--tf-success);
        }

        .status-offline {
            color: var(--tf-error);
        }

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

        .guide-step::before {
            content: '';
            position: absolute;
            left: -4px;
            top: 0;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--tf-primary);
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
    Render the TerraFusion logo with cyberpunk styling.
    """
    # Use a gradient text logo with futuristic styling
    logo_html = """
    <div class="tf-sidebar-header">
        <div class="tf-sidebar-title">TerraFusion AI</div>
    </div>
    """
    
    st.sidebar.markdown(logo_html, unsafe_allow_html=True)