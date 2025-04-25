"""
Navigation Components Module

This module provides standardized navigation components for the TerraFusion UI.
"""
import streamlit as st
import os
from typing import List, Tuple, Dict, Optional, Union, Any

# Define the navigation structure
NAVIGATION = [
    {"name": "Home", "icon": "🏠", "url": "/"},
    {"name": "Sync Service", "icon": "📊", "url": "/Sync_Service_Dashboard"},
    {"name": "Code Analysis", "icon": "🔍", "url": "/Code_Analysis_Dashboard"},
    {"name": "Agent Orchestration", "icon": "🤖", "url": "/Agent_Orchestration"},
    {"name": "Workflow Visualization", "icon": "📈", "url": "/Workflow_Visualization"},
    {"name": "Repository Analysis", "icon": "🔄", "url": "/Repository_Analysis"},
    {"name": "AI Chat Interface", "icon": "💬", "url": "/AI_Chat_Interface"},
]

def get_current_page_name() -> str:
    """
    Get the current page name from the URL.
    
    Returns:
        str: The current page name
    """
    # Try to get the current script path
    try:
        # Get the script path from the session state if it's been set
        if 'current_page' in st.session_state:
            return st.session_state.current_page
        
        # Otherwise use the current main script path
        import inspect
        import os
        current_frame = inspect.currentframe()
        while current_frame:
            if 'self' in current_frame.f_locals and hasattr(current_frame.f_locals['self'], '__module__'):
                if current_frame.f_locals['self'].__module__ == 'streamlit.runtime.scriptrunner.script_runner':
                    if hasattr(current_frame.f_locals['self'], '_main_script_path'):
                        script_path = current_frame.f_locals['self']._main_script_path
                        page_name = os.path.splitext(os.path.basename(script_path))[0]
                        # Special case for main app
                        if page_name in ["app", "combined_app", "enhanced_app"]:
                            return "Home"
                        return page_name
            current_frame = current_frame.f_back
        
        # If we can't determine the page name, default to Home
        return "Home"
    except Exception as e:
        # If anything goes wrong, default to Home
        print(f"Error getting current page name: {e}")
        return "Home"

def render_sidebar_navigation():
    """
    Render the sidebar navigation with the current page highlighted.
    """
    st.sidebar.markdown("## Navigation")
    
    current_page = get_current_page_name()
    
    # If we're on the main page (app.py), change current_page to "Home"
    if current_page in ["app", "combined_app", "enhanced_app"]:
        current_page = "Home"
    
    for nav_item in NAVIGATION:
        page_name = nav_item["name"]
        page_icon = nav_item["icon"]
        page_url = nav_item["url"]
        
        # Check if this is the current page
        is_current = (page_name == current_page) or (
            page_name == "Home" and current_page in ["app", "combined_app", "enhanced_app"]
        ) or (
            page_url.strip('/') in current_page
        )
        
        # Apply the appropriate CSS class based on whether this is the current page
        if is_current:
            st.sidebar.markdown(
                f"""
                <div class="tf-nav-item tf-nav-item-active">
                    <div class="tf-nav-icon">{page_icon}</div>
                    <div>{page_name}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # For non-current items, make them clickable
            if page_url == "/":
                # For home page
                click_action = "window.location.href = '/';"
            else:
                # For other pages
                click_action = f"window.open('/{page_url.strip('/')}', '_self');"
            
            st.sidebar.markdown(
                f"""
                <div class="tf-nav-item" onclick="{click_action}" style="cursor: pointer;">
                    <div class="tf-nav-icon">{page_icon}</div>
                    <div>{page_name}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Add a separator
    st.sidebar.markdown("<hr style='border-color: rgba(0, 229, 255, 0.2); margin: 1.5rem 0;'>", unsafe_allow_html=True)

def render_breadcrumbs(additional_items=None):
    """
    Render breadcrumb navigation for the current page.
    
    Args:
        additional_items: Optional list of additional breadcrumb items as (name, url) tuples
    """
    current_page = get_current_page_name()
    
    # Start with home - use list instead of typed tuples
    breadcrumbs = []
    breadcrumbs.append(["Home", "/"])
    
    # If we're on a subpage, add it to the breadcrumbs
    if current_page not in ["app", "combined_app", "enhanced_app", "Home"]:
        # Find the navigation item for this page
        for nav_item in NAVIGATION:
            if nav_item["name"] == current_page or nav_item["url"].strip('/') in current_page:
                breadcrumbs.append([nav_item["name"], nav_item["url"]])
                break
    
    # Add any additional items
    if additional_items is not None:
        for item in additional_items:
            if (isinstance(item, tuple) or isinstance(item, list)) and len(item) == 2:
                breadcrumbs.append([item[0], item[1]])
    
    # Render the breadcrumbs
    breadcrumb_html = '<div class="tf-breadcrumb">'
    
    for i, breadcrumb in enumerate(breadcrumbs):
        name, url = breadcrumb
        
        # For the last item, don't make it a link and apply the active class
        if i == len(breadcrumbs) - 1:
            breadcrumb_html += f'<div class="tf-breadcrumb-item tf-breadcrumb-active">{name}</div>'
        else:
            breadcrumb_html += f'<div class="tf-breadcrumb-item"><a href="{url}">{name}</a></div>'
    
    breadcrumb_html += '</div>'
    
    st.markdown(breadcrumb_html, unsafe_allow_html=True)

def render_page_header(title, subtitle=None, additional_breadcrumbs=None):
    """
    Render a standardized page header with title, subtitle, and breadcrumbs.
    
    Args:
        title: The page title
        subtitle: Optional subtitle
        additional_breadcrumbs: Optional additional breadcrumb items
    """
    # Render the breadcrumbs
    render_breadcrumbs(additional_breadcrumbs)
    
    # Render the title
    st.markdown(f'<h1 class="tf-page-title">{title}</h1>', unsafe_allow_html=True)
    
    # Render the subtitle if provided
    if subtitle is not None:
        st.markdown(f'<p class="sub-header">{subtitle}</p>', unsafe_allow_html=True)
    
    # Add a separator
    st.markdown('<hr style="border-color: rgba(0, 229, 255, 0.2); margin: 1.5rem 0;">', unsafe_allow_html=True)