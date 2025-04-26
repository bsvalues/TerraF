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
        /* Base color palette - modern cyberpunk/tech theme with minimalist refinements */
        :root {
            /* Primary colors - slightly softer purple for better readability */
            --tf-primary: #7c4dff;
            --tf-primary-light: #b47cff;
            --tf-primary-dark: #3f1dcb;
            
            /* Accent colors - refined teal/cyan */
            --tf-accent: #00e0e0;
            --tf-accent-light: #73ffff;
            --tf-accent-dark: #00b0b0;
            
            /* Background colors - slightly softened for reduced eye strain */
            --tf-background: #121212;
            --tf-card-bg: #1e1e1e;
            --tf-card-bg-hover: #252525;
            --tf-surface: #202020;
            
            /* Text colors - optimized for readability */
            --tf-text: #f8f9fa;
            --tf-text-secondary: rgba(248, 249, 250, 0.85);
            --tf-text-tertiary: rgba(248, 249, 250, 0.65);
            
            /* Border colors - subtle but visible */
            --tf-border: rgba(124, 77, 255, 0.25);
            --tf-border-light: rgba(124, 77, 255, 0.1);
            
            /* Status colors */
            --tf-success: #00e676;
            --tf-warning: #ffea00;
            --tf-error: #ff1744;
            
            /* Effects */
            --tf-shadow: rgba(0, 0, 0, 0.5);
            --tf-glow: rgba(124, 77, 255, 0.35);
            
            /* Spacings for more consistent whitespace */
            --spacing-xs: 0.375rem;
            --spacing-sm: 0.75rem;
            --spacing-md: 1.25rem;
            --spacing-lg: 2rem;
            --spacing-xl: 3rem;
            
            /* Fonts - modern variable font stack */
            --font-sans: 'Inter var', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            --font-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
            
            /* Border radius - more consistent across components */
            --radius-sm: 0.25rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            
            /* Animation timings */
            --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-normal: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Base styles - refined for better readability */
        .stApp {
            background-color: var(--tf-background);
            color: var(--tf-text);
            font-family: var(--font-sans);
            position: relative;
            line-height: 1.5;
            letter-spacing: 0.01em;
        }
        
        /* Subtle background texture - noise effect trend */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.04;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.95' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E"),
                radial-gradient(circle at 10% 20%, rgba(124, 77, 255, 0.02) 0%, transparent 20%),
                radial-gradient(circle at 90% 80%, rgba(0, 224, 224, 0.02) 0%, transparent 20%),
                linear-gradient(135deg, rgba(63, 29, 203, 0.01) 0%, rgba(124, 77, 255, 0.015) 100%);
            pointer-events: none;
            z-index: -1;
        }
        
        /* Refined top accent - subtle but still distinctive */
        .stApp::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--tf-accent-dark), var(--tf-primary), var(--tf-accent), var(--tf-primary-dark));
            z-index: 1000;
            box-shadow: 0 0 8px var(--tf-glow);
            opacity: 0.9;
        }
        
        /* Improved scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--tf-background);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--tf-primary-dark);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--tf-primary);
        }
        
        /* Typography - modern, variable font approach */
        h1, h2, h3, h4, h5, h6 {
            color: var(--tf-primary);
            font-weight: 600;
            margin-bottom: var(--spacing-md);
            line-height: 1.2;
            letter-spacing: -0.02em;
        }
        
        h1 {
            font-size: clamp(2rem, 5vw, 2.5rem);
            background: linear-gradient(90deg, var(--tf-primary-light), var(--tf-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        h2 {
            font-size: clamp(1.5rem, 4vw, 2rem);
            color: var(--tf-text);
            position: relative;
            display: inline-block;
            margin-bottom: var(--spacing-lg);
        }
        
        h2::after {
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            width: 60px;
            height: 2px;
            background: linear-gradient(90deg, var(--tf-primary), var(--tf-accent));
            opacity: 0.8;
        }
        
        h3 {
            font-size: clamp(1.25rem, 3vw, 1.5rem);
        }
        
        /* Paragraph styling */
        p {
            margin-bottom: var(--spacing-md);
            font-size: 1rem;
            line-height: 1.6;
        }
        
        /* Code and pre tags */
        code {
            font-family: var(--font-mono);
            font-size: 0.9em;
            padding: 0.2em 0.4em;
            background-color: rgba(124, 77, 255, 0.1);
            border-radius: 3px;
            color: var(--tf-accent);
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
        
        /* Card component - minimalist with subtle futuristic accents */
        .tf-card {
            background-color: var(--tf-card-bg);
            border: 1px solid var(--tf-border);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            margin-bottom: var(--spacing-lg);
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            transition: all var(--transition-normal);
            backdrop-filter: blur(5px);
        }
        
        /* Subtle edge accent */
        .tf-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 3px;
            height: 100%;
            background: linear-gradient(to bottom, var(--tf-primary), var(--tf-accent));
            opacity: 0.7;
        }
        
        /* Card hover effects - subtle animation */
        .tf-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            border-color: var(--tf-primary-light);
        }
        
        /* Card hover accent animation */
        .tf-card:hover::before {
            opacity: 1;
            background: linear-gradient(to bottom, var(--tf-accent), var(--tf-primary-light));
        }
        
        /* Button styles - modernized design with interactive elements */
        .tf-button, .stButton > button {
            background-color: var(--tf-primary) !important;
            background-image: linear-gradient(135deg, var(--tf-primary), var(--tf-primary-dark)) !important;
            color: white !important;
            font-weight: 500 !important;
            border: none !important;
            padding: 0.6rem 1.25rem !important;
            border-radius: var(--radius-md) !important;
            cursor: pointer !important;
            transition: all var(--transition-fast) !important;
            text-align: center !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            position: relative !important;
            letter-spacing: 0.01em !important;
            font-size: 0.95rem !important;
            overflow: hidden !important;
            box-shadow: 0 4px 10px rgba(124, 77, 255, 0.2) !important;
            z-index: 1 !important;
            width: 100% !important;
        }
        
        /* Button hover effects - subtle glow and lift */
        .tf-button:hover, .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 14px rgba(124, 77, 255, 0.3) !important;
            background-image: linear-gradient(135deg, var(--tf-primary-light), var(--tf-primary)) !important;
        }
        
        /* Button click effect */
        .tf-button:active, .stButton > button:active {
            transform: translateY(1px) !important;
            box-shadow: 0 2px 8px rgba(124, 77, 255, 0.2) !important;
        }
        
        /* Button hover glow effect */
        .tf-button::after, .stButton > button::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0));
            opacity: 0;
            transition: opacity var(--transition-fast);
        }
        
        .tf-button:hover::after, .stButton > button:hover::after {
            opacity: 1;
        }
        
        /* Navigation - refined minimalist style with interactivity */
        .tf-nav-item {
            display: flex;
            align-items: center;
            padding: 0.625rem 1rem;
            color: var(--tf-text-secondary);
            text-decoration: none;
            border-radius: var(--radius-md);
            transition: all var(--transition-fast);
            margin-bottom: 0.25rem;
            position: relative;
            overflow: hidden;
            font-weight: 500;
            font-size: 0.95rem;
            border: 1px solid transparent;
        }
        
        /* Subtle hover effect with animated border indicator */
        .tf-nav-item:hover {
            background-color: rgba(124, 77, 255, 0.08);
            color: var(--tf-text);
            border-color: rgba(124, 77, 255, 0.15);
        }
        
        /* Active state with gradient indicator */
        .tf-nav-item-active {
            background-color: rgba(124, 77, 255, 0.12);
            color: var(--tf-primary-light);
            font-weight: 600;
            border-color: rgba(124, 77, 255, 0.25);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        /* Navigation icon with animation */
        .tf-nav-icon {
            margin-right: 0.625rem;
            font-size: 1.1em;
            opacity: 0.9;
            transition: all var(--transition-fast);
        }
        
        /* Icon animation on hover */
        .tf-nav-item:hover .tf-nav-icon {
            transform: translateX(2px);
            opacity: 1;
            color: var(--tf-primary);
        }
        
        /* Special pulse animation for active item icon */
        .tf-nav-item-active .tf-nav-icon {
            color: var(--tf-primary);
            opacity: 1;
        }
        
        /* Animated indicator dot for active item */
        .tf-nav-item-active::before {
            content: '';
            position: absolute;
            left: 0.375rem;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: var(--tf-primary);
            box-shadow: 0 0 8px var(--tf-primary);
        }
        
        /* Enhanced sidebar header styling */
        .tf-sidebar-header {
            display: flex;
            align-items: center;
            margin-bottom: var(--spacing-lg);
            padding-bottom: var(--spacing-md);
            position: relative;
        }
        
        /* Animated gradient border for header */
        .tf-sidebar-header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent, 
                var(--tf-primary-light),
                var(--tf-accent), 
                var(--tf-primary-light),
                transparent
            );
        }
        
        /* Modern gradient title with subtle animation */
        .tf-sidebar-title {
            font-size: 1.35rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(90deg, var(--tf-primary), var(--tf-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.01em;
            position: relative;
        }
        
        /* Subtle title glow effect */
        .tf-sidebar-title::after {
            content: attr(data-text);
            position: absolute;
            left: 0;
            top: 0;
            z-index: -1;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: blur(8px);
            opacity: 0.3;
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
    # Use a gradient text logo with futuristic styling and glow effect
    logo_html = """
    <div class="tf-sidebar-header">
        <div class="tf-sidebar-title" data-text="TerraFusion AI">TerraFusion AI</div>
    </div>
    """
    
    st.sidebar.markdown(logo_html, unsafe_allow_html=True)