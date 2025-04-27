"""
TerraFusionPlatform Design System

This module centralizes design tokens, components, and styling for consistent UX/UI across the platform.
"""

import streamlit as st

# Color Palette
COLORS = {
    # Primary colors
    "primary": {
        "main": "#7c4dff",  # Primary purple
        "light": "#b47cff", # Lighter purple
        "dark": "#3f1dcb",  # Darker purple
    },
    # Secondary colors
    "secondary": {
        "main": "#00e5ff",  # Cyan
        "light": "#6effff", # Light cyan
        "dark": "#00b2cc", # Dark cyan
    },
    # Neutral colors
    "neutral": {
        "background": "#121212",     # Main background
        "card": "#1e1e1e",           # Card background
        "surface": "#252525",        # Surface background
        "border": "rgba(124, 77, 255, 0.25)", # Border color
    },
    # Text colors
    "text": {
        "primary": "#f8f9fa",       # Primary text
        "secondary": "rgba(248, 249, 250, 0.85)", # Secondary text
        "muted": "rgba(248, 249, 250, 0.65)",     # Muted text
    },
    # Status colors
    "status": {
        "success": "#00e676", # Green
        "warning": "#ffea00", # Yellow
        "error": "#ff1744",   # Red
        "info": "#2196f3",    # Blue
    },
}

# Typography
TYPOGRAPHY = {
    "font_family": "'Inter', sans-serif",
    "heading_1": {
        "size": "2.5rem",
        "weight": "700",
        "line_height": "1.2",
    },
    "heading_2": {
        "size": "2rem",
        "weight": "700",
        "line_height": "1.25",
    },
    "heading_3": {
        "size": "1.5rem",
        "weight": "600",
        "line_height": "1.3",
    },
    "heading_4": {
        "size": "1.25rem",
        "weight": "600",
        "line_height": "1.4",
    },
    "body_large": {
        "size": "1.125rem",
        "weight": "400",
        "line_height": "1.5",
    },
    "body": {
        "size": "1rem",
        "weight": "400",
        "line_height": "1.5",
    },
    "body_small": {
        "size": "0.875rem",
        "weight": "400",
        "line_height": "1.5",
    },
    "caption": {
        "size": "0.75rem",
        "weight": "400",
        "line_height": "1.5",
    },
}

# Spacing
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "xxl": "3rem",
}

# Borders & Shadows
BORDERS = {
    "radius": {
        "sm": "0.25rem",
        "md": "0.5rem",
        "lg": "0.75rem",
        "xl": "1rem",
        "full": "9999px",
    },
    "width": {
        "thin": "1px",
        "medium": "2px",
        "thick": "3px",
    },
}

SHADOWS = {
    "sm": "0 2px 4px rgba(0, 0, 0, 0.1)",
    "md": "0 4px 8px rgba(0, 0, 0, 0.12)",
    "lg": "0 8px 16px rgba(0, 0, 0, 0.14)",
    "xl": "0 12px 24px rgba(0, 0, 0, 0.16)",
}

# Animation
ANIMATION = {
    "duration": {
        "fast": "150ms",
        "medium": "300ms",
        "slow": "500ms",
    },
    "easing": {
        "standard": "cubic-bezier(0.4, 0, 0.2, 1)",
        "accelerate": "cubic-bezier(0.4, 0, 1, 1)",
        "decelerate": "cubic-bezier(0, 0, 0.2, 1)",
    },
}

# z-index
Z_INDEX = {
    "background": -1,
    "base": 0,
    "content": 1,
    "navigation": 100,
    "overlay": 200,
    "modal": 300,
    "toast": 400,
    "tooltip": 500,
}

# Apply Design System
def apply_design_system():
    """Apply the design system to the Streamlit app."""
    st.markdown(f"""
    <style>
        /* General styling */
        .main {{
            background-color: {COLORS["neutral"]["background"]};
            color: {COLORS["text"]["primary"]};
            font-family: {TYPOGRAPHY["font_family"]};
        }}
        
        /* Header styling */
        h1, .h1 {{
            color: {COLORS["primary"]["main"]};
            font-size: {TYPOGRAPHY["heading_1"]["size"]};
            font-weight: {TYPOGRAPHY["heading_1"]["weight"]};
            line-height: {TYPOGRAPHY["heading_1"]["line_height"]};
            margin-bottom: {SPACING["md"]};
        }}
        
        h2, .h2 {{
            color: {COLORS["text"]["primary"]};
            font-size: {TYPOGRAPHY["heading_2"]["size"]};
            font-weight: {TYPOGRAPHY["heading_2"]["weight"]};
            line-height: {TYPOGRAPHY["heading_2"]["line_height"]};
            margin-bottom: {SPACING["sm"]};
        }}
        
        h3, .h3 {{
            color: {COLORS["text"]["primary"]};
            font-size: {TYPOGRAPHY["heading_3"]["size"]};
            font-weight: {TYPOGRAPHY["heading_3"]["weight"]};
            line-height: {TYPOGRAPHY["heading_3"]["line_height"]};
            margin-bottom: {SPACING["sm"]};
        }}
        
        .subheader {{
            color: {COLORS["text"]["secondary"]};
            font-size: {TYPOGRAPHY["body_large"]["size"]};
            margin-bottom: {SPACING["lg"]};
        }}
        
        /* Card styling */
        .tf-card {{
            background-color: {COLORS["neutral"]["card"]};
            border: {BORDERS["width"]["thin"]} solid {COLORS["neutral"]["border"]};
            border-radius: {BORDERS["radius"]["lg"]};
            padding: {SPACING["lg"]};
            margin-bottom: {SPACING["lg"]};
            box-shadow: {SHADOWS["md"]};
            transition: transform {ANIMATION["duration"]["medium"]} {ANIMATION["easing"]["standard"]};
        }}
        
        .tf-card:hover {{
            transform: translateY(-2px);
        }}
        
        /* Phase indicator styling */
        .phase-indicator {{
            display: flex;
            margin-bottom: {SPACING["lg"]};
        }}
        
        .phase-item {{
            flex: 1;
            text-align: center;
            padding: {SPACING["sm"]} 0;
            position: relative;
            background-color: {COLORS["neutral"]["surface"]};
            border: {BORDERS["width"]["thin"]} solid rgba(124, 77, 255, 0.1);
        }}
        
        .phase-item.active {{
            background-color: rgba(124, 77, 255, 0.12);
            border-color: {COLORS["primary"]["main"]};
            color: {COLORS["primary"]["main"]};
            font-weight: 600;
        }}
        
        .phase-item:not(:last-child):after {{
            content: "";
            position: absolute;
            right: -15px;
            top: 50%;
            transform: translateY(-50%);
            width: 30px;
            height: 2px;
            background-color: rgba(124, 77, 255, 0.25);
            z-index: {Z_INDEX["content"]};
        }}
        
        /* Report card styling */
        .report-card {{
            padding: {SPACING["md"]};
            border-radius: {BORDERS["radius"]["md"]};
            background-color: {COLORS["neutral"]["surface"]};
            margin-bottom: {SPACING["sm"]};
            border-left: {BORDERS["width"]["thick"]} solid {COLORS["primary"]["main"]};
        }}
        
        /* Button styling */
        .primary-button {{
            background-color: {COLORS["primary"]["main"]};
            color: white;
            border-radius: {BORDERS["radius"]["md"]};
            border: none;
            padding: 0.6rem 1.25rem;
            font-weight: 500;
            transition: all {ANIMATION["duration"]["medium"]};
        }}
        
        .primary-button:hover {{
            background-color: {COLORS["primary"]["light"]};
            transform: translateY(-2px);
        }}
        
        /* Secondary button */
        .secondary-button {{
            background-color: transparent;
            color: {COLORS["primary"]["main"]};
            border: {BORDERS["width"]["thin"]} solid {COLORS["primary"]["main"]};
            border-radius: {BORDERS["radius"]["md"]};
            padding: 0.6rem 1.25rem;
            font-weight: 500;
            transition: all {ANIMATION["duration"]["medium"]};
        }}
        
        .secondary-button:hover {{
            background-color: rgba(124, 77, 255, 0.1);
            transform: translateY(-2px);
        }}
        
        /* Alert styling */
        .tf-alert {{
            padding: {SPACING["md"]};
            border-radius: {BORDERS["radius"]["md"]};
            margin-bottom: {SPACING["md"]};
            position: relative;
        }}
        
        .tf-alert.success {{
            background-color: rgba(0, 230, 118, 0.1);
            border-left: {BORDERS["width"]["thick"]} solid {COLORS["status"]["success"]};
        }}
        
        .tf-alert.warning {{
            background-color: rgba(255, 234, 0, 0.1);
            border-left: {BORDERS["width"]["thick"]} solid {COLORS["status"]["warning"]};
        }}
        
        .tf-alert.error {{
            background-color: rgba(255, 23, 68, 0.1);
            border-left: {BORDERS["width"]["thick"]} solid {COLORS["status"]["error"]};
        }}
        
        .tf-alert.info {{
            background-color: rgba(33, 150, 243, 0.1);
            border-left: {BORDERS["width"]["thick"]} solid {COLORS["status"]["info"]};
        }}
        
        /* Status indicator */
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: {SPACING["sm"]};
        }}
        
        .status-success {{
            background-color: {COLORS["status"]["success"]};
            box-shadow: 0 0 8px {COLORS["status"]["success"]};
        }}
        
        .status-warning {{
            background-color: {COLORS["status"]["warning"]};
            box-shadow: 0 0 8px {COLORS["status"]["warning"]};
        }}
        
        .status-error {{
            background-color: {COLORS["status"]["error"]};
            box-shadow: 0 0 8px {COLORS["status"]["error"]};
        }}
        
        /* Timeline styling */
        .timeline-container {{
            position: relative;
            margin-left: 2rem;
            padding-left: 2rem;
            border-left: 2px solid rgba(124, 77, 255, 0.25);
        }}
        
        .timeline-item {{
            position: relative;
            margin-bottom: {SPACING["lg"]};
        }}
        
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -2.3rem;
            top: 6px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: {COLORS["primary"]["main"]};
            box-shadow: 0 0 8px rgba(124, 77, 255, 0.3);
        }}
        
        /* Table styling */
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background-color: {COLORS["neutral"]["surface"]};
            padding: {SPACING["sm"]} {SPACING["md"]};
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: {SPACING["sm"]} {SPACING["md"]};
            border-top: {BORDERS["width"]["thin"]} solid rgba(124, 77, 255, 0.1);
        }}
        
        tr:hover td {{
            background-color: rgba(124, 77, 255, 0.05);
        }}
        
        /* Logo styling */
        .logo-container {{
            display: flex;
            align-items: center;
            margin-bottom: {SPACING["xl"]};
        }}
        
        .logo-text {{
            font-size: {TYPOGRAPHY["heading_3"]["size"]};
            font-weight: {TYPOGRAPHY["heading_1"]["weight"]};
            margin-left: {SPACING["sm"]};
            background: linear-gradient(90deg, {COLORS["primary"]["main"]}, {COLORS["secondary"]["main"]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        /* Loader */
        .tf-loader {{
            width: 40px;
            height: 40px;
            border: 3px solid rgba(124, 77, 255, 0.2);
            border-top: 3px solid {COLORS["primary"]["main"]};
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Accessibility improvements */
        a:focus, button:focus, [role="button"]:focus {{
            outline: 2px solid {COLORS["primary"]["main"]};
            outline-offset: 2px;
        }}
        
        /* Make Streamlit components consistent with our design system */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {{
            background-color: {COLORS["neutral"]["surface"]};
            color: {COLORS["text"]["primary"]};
            border-color: rgba(124, 77, 255, 0.25);
            border-radius: {BORDERS["radius"]["md"]};
        }}
        
        /* Customize checkbox styling */
        .stCheckbox > div > label > div[role="checkbox"] {{
            background-color: {COLORS["neutral"]["card"]};
            border-color: {COLORS["primary"]["main"]};
        }}
        
        /* Customize slider styling */
        .stSlider > div > div > div > div {{
            background-color: {COLORS["primary"]["main"]};
        }}
        
        /* Customize the sidebar */
        [data-testid="stSidebar"] {{
            background-color: {COLORS["neutral"]["background"]};
            border-right: {BORDERS["width"]["thin"]} solid rgba(124, 77, 255, 0.25);
        }}
        
        /* Responsive improvements */
        @media (max-width: 768px) {{
            .tf-card {{
                padding: {SPACING["md"]};
            }}
            
            .timeline-container {{
                margin-left: 1rem;
                padding-left: 1rem;
            }}
            
            .timeline-item::before {{
                left: -1.3rem;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

# Component functions
def card(title, content, is_clickable=False):
    """Render a styled card with title and content."""
    card_html = f"""
    <div class="tf-card{' clickable' if is_clickable else ''}">
        <h3>{title}</h3>
        <div>{content}</div>
    </div>
    """
    return st.markdown(card_html, unsafe_allow_html=True)

def alert(message, alert_type="info"):
    """Render an alert message with the specified type."""
    alert_html = f"""
    <div class="tf-alert {alert_type}">
        {message}
    </div>
    """
    return st.markdown(alert_html, unsafe_allow_html=True)

def status_badge(status, text):
    """Render a status badge with the specified status and text."""
    status_class = {
        "success": "status-success",
        "warning": "status-warning",
        "error": "status-error"
    }.get(status, "status-success")
    
    badge_html = f"""
    <div style="display: inline-flex; align-items: center;">
        <span class="status-indicator {status_class}"></span>
        <span>{text}</span>
    </div>
    """
    return st.markdown(badge_html, unsafe_allow_html=True)

def loading_indicator(message="Loading..."):
    """Render a loading indicator with an optional message."""
    loader_html = f"""
    <div style="text-align: center; padding: {SPACING["md"]} 0;">
        <div class="tf-loader"></div>
        <p style="margin-top: {SPACING["sm"]}; color: {COLORS["text"]["secondary"]};">{message}</p>
    </div>
    """
    return st.markdown(loader_html, unsafe_allow_html=True)

def empty_state(message, icon="📦"):
    """Render an empty state with message and icon."""
    empty_html = f"""
    <div style="text-align: center; padding: {SPACING["xl"]} 0;">
        <div style="font-size: 3rem; margin-bottom: {SPACING["md"]};">{icon}</div>
        <p style="color: {COLORS["text"]["secondary"]};">{message}</p>
    </div>
    """
    return st.markdown(empty_html, unsafe_allow_html=True)

def display_logo():
    """Display the TerraFusion logo and title."""
    logo_html = f"""
    <div class="logo-container">
        <div style="font-size: 2rem;">🚀</div>
        <div class="logo-text">TerraFusionPlatform</div>
    </div>
    """
    return st.markdown(logo_html, unsafe_allow_html=True)

def section_title(title, description=None):
    """Display a section title with optional description."""
    if description:
        header_html = f"""
        <h2 class="h2">{title}</h2>
        <p class="subheader">{description}</p>
        """
    else:
        header_html = f"""
        <h2 class="h2">{title}</h2>
        """
    return st.markdown(header_html, unsafe_allow_html=True)