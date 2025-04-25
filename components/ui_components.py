"""
UI Components Module

This module provides reusable UI components for the TerraFusion application.
"""
import streamlit as st
from typing import List, Dict, Any, Optional, Union
import datetime

def metric_card(title: str, value: Union[str, int, float], unit: str = "", delta: Optional[float] = None, delta_suffix: str = "%"):
    """
    Render a metric card with title, value, unit, and optional delta.
    
    Args:
        title: The title of the metric
        value: The value to display
        unit: Optional unit to display after the value
        delta: Optional delta value for showing change
        delta_suffix: Suffix for the delta value
    """
    # Format the value if it's a numeric type
    if isinstance(value, (int, float)):
        if isinstance(value, int):
            value_str = f"{value:,}"
        else:
            value_str = f"{value:,.2f}".rstrip('0').rstrip('.') if value % 1 != 0 else f"{int(value):,}"
    else:
        value_str = str(value)
    
    # Determine the delta color class
    delta_class = ""
    delta_arrow = ""
    if delta is not None:
        if delta > 0:
            delta_class = "tf-success"
            delta_arrow = "↑"
        elif delta < 0:
            delta_class = "tf-error"
            delta_arrow = "↓"
        else:
            delta_class = "tf-text-tertiary"
            delta_arrow = "→"
    
    # Build the HTML for the metric card
    html = f"""
    <div class="tf-metric">
        <div class="tf-metric-title">{title}</div>
        <div class="tf-metric-value">{value_str}</div>
        <div class="tf-metric-unit">{unit}"""
    
    # Add delta if provided
    if delta is not None:
        html += f' <span class="{delta_class}">{delta_arrow} {abs(delta)}{delta_suffix}</span>'
    
    html += """</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def feature_card(title: str, description: str, icon: str = "🔍", on_click=None):
    """
    Render a feature card with title, description, and icon.
    
    Args:
        title: The title of the feature
        description: The description of the feature
        icon: The icon to display
        on_click: Optional callback for when the card is clicked
    """
    html = f"""
    <div class="tf-card feature-card">
        <div style="font-size: 2rem; color: var(--tf-primary); margin-bottom: 1rem;">{icon}</div>
        <div class="tf-card-title">{title}</div>
        <div style="color: var(--tf-text-secondary);">{description}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)
    
    if on_click:
        # This is a placeholder for click handling - in Streamlit we'd use columns with buttons
        st.button(f"Open {title}", key=f"btn_{title.lower().replace(' ', '_')}", on_click=on_click)

def status_indicator(status: str, label: str):
    """
    Render a status indicator with a color-coded dot and label.
    
    Args:
        status: The status to display (online, offline, warning)
        label: The label text to display
    """
    if status.lower() == "online":
        status_class = "tf-status-online"
    elif status.lower() == "offline":
        status_class = "tf-status-offline"
    elif status.lower() == "warning":
        status_class = "tf-status-warning"
    else:
        status_class = "tf-status-offline"
    
    html = f"""
    <div class="tf-status {status_class}">
        {label}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def activity_feed(activities: List[Dict[str, Any]]):
    """
    Render an activity feed with timestamps and content.
    
    Args:
        activities: List of activity items with 'time' and 'text' keys
    """
    html = '<div class="tf-activity">'
    
    for activity in activities:
        # Format the time if it's a datetime object
        if isinstance(activity['time'], datetime.datetime):
            time_str = activity['time'].strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = str(activity['time'])
        
        html += f"""
        <div class="tf-activity-item">
            <div class="tf-activity-time">{time_str}</div>
            <div class="tf-activity-content">{activity['text']}</div>
        </div>
        """
    
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)

def alert_item(text: str, severity: str = "medium", time: str = None):
    """
    Render an alert item with text, severity, and time.
    
    Args:
        text: The alert text
        severity: The severity level (high, medium, low)
        time: Optional time string
    """
    if severity.lower() == "high":
        severity_class = "alert-high"
        icon = "🔴"
    elif severity.lower() == "medium":
        severity_class = "alert-medium"
        icon = "🟠"
    else:
        severity_class = "alert-low"
        icon = "🟢"
    
    html = f"""
    <div class="alert-item {severity_class}">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <div style="font-weight: 600;">{icon} {severity.capitalize()} Priority</div>
            {f'<div style="color: var(--tf-text-tertiary); font-size: 0.8rem;">{time}</div>' if time else ''}
        </div>
        <div>{text}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def section_header(title: str):
    """
    Render a section header with a title.
    
    Args:
        title: The section title
    """
    st.markdown(f'<h2 class="section-header">{title}</h2>', unsafe_allow_html=True)

def loading_placeholder(text: str = "Loading..."):
    """
    Render a loading placeholder with a pulsing animation.
    
    Args:
        text: The loading text to display
    """
    html = f"""
    <div class="tf-loading" style="padding: 1rem; text-align: center; color: var(--tf-text-secondary);">
        {text}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)