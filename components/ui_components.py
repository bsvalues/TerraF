"""
UI Components Module

This module provides reusable UI components for the TerraFusion UI.
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Union, Optional, Tuple

def render_card(title: str, content: str, icon: Optional[str] = None):
    """
    Render a card with a title, content, and optional icon.
    
    Args:
        title: Card title
        content: Card content
        icon: Optional icon (emoji or font awesome)
    """
    if icon:
        icon_html = f'<div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>'
    else:
        icon_html = ''
    
    st.markdown(
        f"""
        <div style="background-color: var(--tf-card-bg); border: 1px solid rgba(124, 77, 255, 0.25);
                    border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; position: relative;">
            {icon_html}
            <div style="font-size: 1.25rem; font-weight: 600; color: #7c4dff; margin-bottom: 0.75rem;">
                {title}
            </div>
            <div style="color: rgba(248, 249, 250, 0.85);">
                {content}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_metric_card(title: str, value: Union[str, int, float], unit: Optional[str] = None, 
                      icon: Optional[str] = None, trend: Optional[float] = None):
    """
    Render a metric card showing a single KPI or metric.
    
    Args:
        title: Metric title
        value: Metric value
        unit: Optional unit of measurement
        icon: Optional icon (emoji or font awesome)
        trend: Optional trend value (positive for up, negative for down)
    """
    # Format the trend if provided
    if trend is not None:
        if trend > 0:
            trend_html = f'<span style="color: #00e676; font-size: 0.875rem; margin-left: 0.5rem;">+{trend}%</span>'
        elif trend < 0:
            trend_html = f'<span style="color: #ff1744; font-size: 0.875rem; margin-left: 0.5rem;">{trend}%</span>'
        else:
            trend_html = f'<span style="color: #ffea00; font-size: 0.875rem; margin-left: 0.5rem;">0%</span>'
    else:
        trend_html = ''
    
    # Add the unit if provided
    if unit:
        unit_html = f'<span style="font-size: 0.875rem; color: rgba(248, 249, 250, 0.65); margin-left: 0.25rem;">{unit}</span>'
    else:
        unit_html = ''
    
    # Add the icon if provided
    if icon:
        icon_html = f'<div style="font-size: 1.25rem; margin-bottom: 0.5rem; color: #7c4dff;">{icon}</div>'
    else:
        icon_html = ''
    
    st.markdown(
        f"""
        <div style="background-color: var(--tf-card-bg); border: 1px solid rgba(124, 77, 255, 0.25); 
                    border-radius: 0.75rem; padding: 1.25rem; text-align: center; height: 100%;">
            {icon_html}
            <div style="color: rgba(248, 249, 250, 0.65); font-size: 0.875rem; margin-bottom: 0.5rem;">
                {title}
            </div>
            <div style="font-size: 2rem; font-weight: 700; color: #7c4dff; margin-bottom: 0.25rem;">
                {value}{unit_html}{trend_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_alert(message: str, level: str = "info", dismissible: bool = False):
    """
    Render an alert message with appropriate styling based on level.
    
    Args:
        message: Alert message
        level: Alert level ('info', 'success', 'warning', 'error')
        dismissible: Whether the alert can be dismissed
    """
    # Set the color based on the level
    if level == "success":
        color = "#00e676"
        icon = "✅"
    elif level == "warning":
        color = "#ffea00"
        icon = "⚠️"
    elif level == "error":
        color = "#ff1744"
        icon = "❌"
    else:  # info
        color = "#7c4dff"
        icon = "ℹ️"
    
    # Generate a unique ID for the alert if it's dismissible
    if dismissible:
        alert_id = f"alert_{hash(message) % 10000}"
        dismiss_button = f"""
        <span style="cursor: pointer; float: right;" 
              onclick="document.getElementById('{alert_id}').style.display='none'">
            ✕
        </span>
        """
        div_id = f'id="{alert_id}"'
    else:
        dismiss_button = ""
        div_id = ""
    
    st.markdown(
        f"""
        <div {div_id} style="background-color: rgba(30, 30, 30, 0.5); border-left: 3px solid {color};
                    border-radius: 0.5rem; padding: 0.75rem; margin-bottom: 1rem;">
            {dismiss_button}
            <div style="display: flex; align-items: flex-start;">
                <div style="margin-right: 0.5rem;">{icon}</div>
                <div>{message}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_info_tooltip(content: str, tooltip: str):
    """
    Render text with an info tooltip on hover.
    
    Args:
        content: The visible content
        tooltip: Tooltip text shown on hover
    """
    st.markdown(
        f"""
        <span style="position: relative; display: inline-block; cursor: help;"
              title="{tooltip}">
            {content}
            <span style="font-size: 0.8em; margin-left: 0.25rem; color: rgba(124, 77, 255, 0.7);">ⓘ</span>
        </span>
        """,
        unsafe_allow_html=True
    )

def render_tabs(tabs: List[Dict[str, str]], default_tab: int = 0):
    """
    Render custom tabs with styling matching the design system.
    
    Args:
        tabs: List of tab dicts with 'label' and 'content' keys
        default_tab: Index of the default active tab (0-based)
    """
    # Generate unique IDs for each tab
    tab_ids = [f"tab_{i}_{hash(tab['label']) % 10000}" for i, tab in enumerate(tabs)]
    
    # Create the tab header
    tab_header = '<div style="display: flex; border-bottom: 1px solid rgba(124, 77, 255, 0.25); margin-bottom: 1rem;">'
    
    for i, tab in enumerate(tabs):
        active_class = "font-weight: 600; color: #7c4dff; border-bottom: 2px solid #7c4dff;" if i == default_tab else ""
        tab_header += f"""
        <div style="padding: 0.5rem 1rem; cursor: pointer; {active_class}"
             onclick="activateTab('{tab_ids[i]}')">
            {tab['label']}
        </div>
        """
    
    tab_header += '</div>'
    
    # Create the tab content containers
    tab_content = ''
    for i, tab in enumerate(tabs):
        display = "block" if i == default_tab else "none"
        tab_content += f"""
        <div id="{tab_ids[i]}" style="display: {display};">
            {tab['content']}
        </div>
        """
    
    # Add JavaScript for tab switching
    tab_js = """
    <script>
    function activateTab(tabId) {
        // Hide all tab content
        var tabContents = document.querySelectorAll('[id^="tab_"]');
        tabContents.forEach(function(tab) {
            tab.style.display = 'none';
        });
        
        // Show the selected tab content
        document.getElementById(tabId).style.display = 'block';
        
        // Update tab header styling
        var tabHeaders = document.querySelectorAll('[onclick^="activateTab"]');
        tabHeaders.forEach(function(header) {
            if (header.getAttribute('onclick').includes(tabId)) {
                header.style.fontWeight = '600';
                header.style.color = '#7c4dff';
                header.style.borderBottom = '2px solid #7c4dff';
            } else {
                header.style.fontWeight = 'normal';
                header.style.color = '';
                header.style.borderBottom = 'none';
            }
        });
    }
    </script>
    """
    
    # Combine everything and render
    st.markdown(
        tab_header + tab_content + tab_js,
        unsafe_allow_html=True
    )

def render_progress_bar(value: float, max_value: float = 100, 
                      label: Optional[str] = None, style: str = "default"):
    """
    Render a progress bar with TerraFusion styling.
    
    Args:
        value: Current value
        max_value: Maximum value (100 by default)
        label: Optional label to display with the progress bar
        style: Style variant ('default', 'success', 'warning', 'error')
    """
    # Calculate percentage
    percentage = min(100, max(0, (value / max_value) * 100))
    
    # Determine color based on style
    if style == "success":
        color = "#00e676"
    elif style == "warning":
        color = "#ffea00"
    elif style == "error":
        color = "#ff1744"
    else:  # default
        color = "#7c4dff"
    
    # Label display
    label_html = f'<div style="margin-bottom: 0.25rem;">{label}</div>' if label else ''
    
    # Value display
    value_html = f'<div style="text-align: right; font-size: 0.875rem; color: rgba(248, 249, 250, 0.85);">{value}/{max_value}</div>'
    
    st.markdown(
        f"""
        {label_html}
        <div style="margin-bottom: 1rem;">
            <div style="height: 0.5rem; background-color: rgba(30, 30, 30, 0.5); 
                        border-radius: 0.25rem; margin-bottom: 0.25rem;">
                <div style="height: 100%; width: {percentage}%; background-color: {color}; 
                            border-radius: 0.25rem;"></div>
            </div>
            {value_html}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_code_block(code: str, language: str = "python"):
    """
    Render a code block with syntax highlighting.
    
    Args:
        code: The code to display
        language: Programming language for syntax highlighting
    """
    # Add syntax highlighting with a dark theme
    st.markdown(
        f"""
        <pre style="background-color: #1a1a1a; padding: 1rem; border-radius: 0.5rem; 
                    overflow-x: auto; margin-bottom: 1rem; font-family: monospace; 
                    border-left: 3px solid #7c4dff;">
            <code class="language-{language}">{code}</code>
        </pre>
        """,
        unsafe_allow_html=True
    )

def render_tag(text: str, color: Optional[str] = None, size: str = "medium"):
    """
    Render a tag/badge with the specified text and styling.
    
    Args:
        text: Tag text
        color: Tag color (optional, uses primary color if not specified)
        size: Tag size ('small', 'medium', 'large')
    """
    # Determine the size
    if size == "small":
        padding = "0.2rem 0.4rem"
        font_size = "0.7rem"
    elif size == "large":
        padding = "0.4rem 0.8rem"
        font_size = "0.9rem"
    else:  # medium (default)
        padding = "0.25rem 0.5rem"
        font_size = "0.8rem"
    
    # Use the provided color or default to primary
    bg_color = color if color else "rgba(124, 77, 255, 0.15)"
    text_color = color if color else "#7c4dff"
    
    st.markdown(
        f"""
        <span style="display: inline-block; padding: {padding}; background-color: {bg_color}; 
                     color: {text_color}; border-radius: 0.35rem; font-weight: 500; 
                     font-size: {font_size};">
            {text}
        </span>
        """,
        unsafe_allow_html=True
    )

def render_timeline(events: List[Dict[str, Any]]):
    """
    Render a vertical timeline of events.
    
    Args:
        events: List of event dicts with 'time', 'title', and 'description' keys
    """
    html = '<div style="position: relative; padding-left: 2rem; margin-bottom: 1.5rem;">'
    
    # Add each event to the timeline
    for event in events:
        html += f"""
        <div style="margin-bottom: 1.5rem; position: relative;">
            <!-- Timeline line -->
            <div style="position: absolute; top: 0; bottom: -1.5rem; left: -1.5rem; width: 2px; 
                        background-color: rgba(124, 77, 255, 0.25);"></div>
            
            <!-- Timeline dot -->
            <div style="position: absolute; left: -1.625rem; top: 0.25rem; width: 0.75rem; 
                        height: 0.75rem; border-radius: 50%; background-color: #7c4dff;"></div>
            
            <!-- Event time -->
            <div style="font-size: 0.8rem; color: rgba(248, 249, 250, 0.65); margin-bottom: 0.25rem;">
                {event['time']}
            </div>
            
            <!-- Event title -->
            <div style="font-weight: 600; margin-bottom: 0.25rem; color: var(--tf-text);">
                {event['title']}
            </div>
            
            <!-- Event description -->
            <div style="color: rgba(248, 249, 250, 0.85);">
                {event.get('description', '')}
            </div>
        </div>
        """
    
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)

def create_gradient_chart(data, title=None, x_label=None, y_label=None, color='#7c4dff'):
    """
    Create a line chart with gradient fill beneath the line.
    
    Args:
        data: Data for the chart (can be a list, Series, or DataFrame)
        title: Chart title
        x_label: Label for x-axis
        y_label: Label for y-axis
        color: Base color for the gradient
        
    Returns:
        fig: Matplotlib figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Convert data to appropriate format if needed
    if isinstance(data, pd.DataFrame) or isinstance(data, pd.Series):
        y = data.values
        x = range(len(y))
    else:
        y = data
        x = range(len(y))
    
    # Plot the line
    ax.plot(x, y, color=color, linewidth=2)
    
    # Create gradient fill
    # Create gradient fill beneath the line
    gradient = np.linspace(0, 1, 100)
    gradient = np.vstack((gradient, gradient))
    
    # Customize colors for dark theme
    ax.set_facecolor('#1e1e1e')
    fig.patch.set_facecolor('#1e1e1e')
    
    # Fill the area beneath the line with a gradient
    ax.fill_between(x, y, color=color, alpha=0.2)
    
    # Set the title and labels if provided
    if title:
        ax.set_title(title, color='white', fontsize=14)
    if x_label:
        ax.set_xlabel(x_label, color='white')
    if y_label:
        ax.set_ylabel(y_label, color='white')
    
    # Customize the grid
    ax.grid(True, linestyle='--', alpha=0.2)
    
    # Customize the ticks
    ax.tick_params(colors='white')
    
    # Customize the spines
    for spine in ax.spines.values():
        spine.set_color('gray')
        spine.set_alpha(0.3)
    
    plt.tight_layout()
    
    return fig