"""
TerraFusion Platform - Main Application

This is the main entry point for the TerraFusion Platform, providing a comprehensive 
DevOps dashboard and access to various platform features. The dashboard offers real-time
visibility into system components, workflows, and operational metrics.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import time
import plotly.graph_objects as go
import plotly.express as px
from bridge import bridge
from components.navigation import render_sidebar_navigation, render_page_header
from components.styling import apply_terraflow_style
from components.ui_components import render_card, render_metric_card, render_alert, render_info_tooltip

# Configure the Streamlit page
st.set_page_config(
    page_title="TerraFusion Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply TerraFusion styling
apply_terraflow_style()

# Initialize session state for dashboard data
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    
if 'system_status' not in st.session_state:
    # Demo status data - this would come from actual monitoring systems in production
    st.session_state.system_status = {
        "agent_pool": {
            "total": 12,
            "active": 8,
            "idle": 3,
            "error": 1,
            "health": 0.92  # 92% healthy
        },
        "workflows": {
            "total": 5,
            "active": 3,
            "completed": 16,
            "failed": 2,
            "success_rate": 0.89  # 89% success rate
        },
        "system_resources": {
            "cpu_usage": 42,
            "memory_usage": 38,
            "disk_usage": 56,
            "network_load": 27
        },
        "services": [
            {"name": "API Gateway", "status": "operational", "response_time": 42, "uptime": 99.98},
            {"name": "Auth Service", "status": "operational", "response_time": 38, "uptime": 99.95},
            {"name": "Repository Service", "status": "operational", "response_time": 85, "uptime": 99.90},
            {"name": "Analysis Service", "status": "operational", "response_time": 120, "uptime": 99.85},
            {"name": "Protocol Server", "status": "degraded", "response_time": 350, "uptime": 98.50}
        ],
        "recent_activity": [
            {"timestamp": datetime.now() - timedelta(minutes=2), "service": "Documentation Agent", "action": "Generated API documentation", "status": "success"},
            {"timestamp": datetime.now() - timedelta(minutes=12), "service": "Code Analyzer", "action": "Completed code analysis", "status": "success"},
            {"timestamp": datetime.now() - timedelta(minutes=28), "service": "Workflow Mapper", "action": "Created workflow visualization", "status": "success"},
            {"timestamp": datetime.now() - timedelta(minutes=45), "service": "Protocol Server", "action": "Processed 250 messages", "status": "warning", "message": "High latency detected"},
            {"timestamp": datetime.now() - timedelta(hours=1, minutes=15), "service": "AI Integration Agent", "action": "Integrated OpenAI model", "status": "success"}
        ],
        "pipeline_status": [
            {"name": "Code Analysis", "stage": "completed", "duration": 45, "success_rate": 100},
            {"name": "Architecture Validation", "stage": "completed", "duration": 78, "success_rate": 100},
            {"name": "Workflow Optimization", "stage": "in_progress", "duration": 32, "success_rate": None},
            {"name": "Documentation Generation", "stage": "pending", "duration": None, "success_rate": None},
            {"name": "Integration Testing", "stage": "pending", "duration": None, "success_rate": None}
        ]
    }

if 'performance_metrics' not in st.session_state:
    # Demo performance data with timestamps over the last 24 hours
    hours = 24
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]
    cpu_values = [35 + 15 * np.sin(i/4) + np.random.randint(-5, 5) for i in range(hours)]
    memory_values = [40 + 10 * np.sin(i/6 + 2) + np.random.randint(-3, 7) for i in range(hours)]
    response_values = [120 + 80 * np.sin(i/8) + np.random.randint(-30, 50) for i in range(hours)]
    throughput_values = [250 + 100 * np.sin(i/6) + np.random.randint(-20, 30) for i in range(hours)]
    
    st.session_state.performance_metrics = {
        "timestamps": timestamps,
        "cpu_usage": cpu_values,
        "memory_usage": memory_values,
        "response_time": response_values,
        "throughput": throughput_values
    }

# Render the sidebar navigation
render_sidebar_navigation()

# Main content
render_page_header(
    "TerraFusion DevOps Dashboard",
    "Comprehensive platform monitoring and operational analytics"
)

# Create a system overview section
st.markdown('<div class="section-header">System Overview</div>', unsafe_allow_html=True)

# Quick metrics in a 4-column layout
col1, col2, col3, col4 = st.columns(4)

with col1:
    active_agents = st.session_state.system_status["agent_pool"]["active"]
    total_agents = st.session_state.system_status["agent_pool"]["total"]
    agent_trend = ((active_agents / total_agents) - 0.5) * 100  # Demo trend
    
    st.markdown(
        render_metric_card(
            "Active Agents", 
            active_agents, 
            f"of {total_agents}",
            trend=agent_trend
        ),
        unsafe_allow_html=True
    )

with col2:
    active_workflows = st.session_state.system_status["workflows"]["active"]
    completed_workflows = st.session_state.system_status["workflows"]["completed"]
    workflow_trend = 10.5  # Demo trend
    
    st.markdown(
        render_metric_card(
            "Active Workflows", 
            active_workflows, 
            f"({completed_workflows} completed)",
            trend=workflow_trend
        ),
        unsafe_allow_html=True
    )

with col3:
    success_rate = st.session_state.system_status["workflows"]["success_rate"] * 100
    trend = 2.5  # Demo trend
    health_status = "healthy" if success_rate > 90 else "warning" if success_rate > 80 else "critical"
    
    st.markdown(
        render_metric_card(
            "Success Rate", 
            f"{success_rate:.1f}", 
            "%",
            trend=trend,
            health_status=health_status
        ),
        unsafe_allow_html=True
    )

with col4:
    # Get real API status
    api_status = bridge.get_api_status()
    status_value = "Online" if api_status.get("success", False) else "Offline"
    status_health = "healthy" if api_status.get("success", False) else "critical"
    
    st.markdown(
        render_metric_card(
            "API Status", 
            status_value, 
            "",
            health_status=status_health
        ),
        unsafe_allow_html=True
    )

# System resource section with performance charts
st.markdown('<div class="section-header">System Resources & Performance</div>', unsafe_allow_html=True)

# Create performance chart tabs
performance_tabs = st.tabs(["Resource Usage", "Response Metrics", "Service Health"])

with performance_tabs[0]:
    # Create line charts for CPU and Memory usage
    cpu_df = pd.DataFrame({
        'Time': st.session_state.performance_metrics["timestamps"],
        'CPU Usage (%)': st.session_state.performance_metrics["cpu_usage"]
    })
    
    memory_df = pd.DataFrame({
        'Time': st.session_state.performance_metrics["timestamps"],
        'Memory Usage (%)': st.session_state.performance_metrics["memory_usage"]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_cpu = px.line(cpu_df, x='Time', y='CPU Usage (%)', 
                         title='CPU Utilization (Last 24 Hours)')
        fig_cpu.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(248,249,250,0.85)'),
            margin=dict(l=10, r=10, t=40, b=10),
            height=300
        )
        fig_cpu.update_traces(line=dict(color='#7c4dff'))
        st.plotly_chart(fig_cpu, use_container_width=True)
    
    with col2:
        fig_mem = px.line(memory_df, x='Time', y='Memory Usage (%)', 
                         title='Memory Utilization (Last 24 Hours)')
        fig_mem.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(248,249,250,0.85)'),
            margin=dict(l=10, r=10, t=40, b=10),
            height=300
        )
        fig_mem.update_traces(line=dict(color='#00e0e0'))
        st.plotly_chart(fig_mem, use_container_width=True)
    
    # Current resource usage gauges
    st.markdown("### Current Resource Utilization")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_current = st.session_state.system_status["system_resources"]["cpu_usage"]
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = cpu_current,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "CPU Usage"},
            gauge = {
                'axis': {'range': [0, 100], 'tickcolor': "rgba(248,249,250,0.5)"},
                'bar': {'color': "#7c4dff"},
                'bgcolor': "rgba(0,0,0,0)",
                'bordercolor': "rgba(248,249,250,0.1)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(0,230,118,0.15)'},
                    {'range': [50, 80], 'color': 'rgba(255,234,0,0.15)'},
                    {'range': [80, 100], 'color': 'rgba(255,23,68,0.15)'}
                ],
            }
        ))
        fig.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(248,249,250,0.85)")
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        memory_current = st.session_state.system_status["system_resources"]["memory_usage"]
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = memory_current,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Memory Usage"},
            gauge = {
                'axis': {'range': [0, 100], 'tickcolor': "rgba(248,249,250,0.5)"},
                'bar': {'color': "#00e0e0"},
                'bgcolor': "rgba(0,0,0,0)",
                'bordercolor': "rgba(248,249,250,0.1)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(0,230,118,0.15)'},
                    {'range': [50, 80], 'color': 'rgba(255,234,0,0.15)'},
                    {'range': [80, 100], 'color': 'rgba(255,23,68,0.15)'}
                ],
            }
        ))
        fig.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(248,249,250,0.85)")
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col3:
        disk_current = st.session_state.system_status["system_resources"]["disk_usage"]
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = disk_current,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Disk Usage"},
            gauge = {
                'axis': {'range': [0, 100], 'tickcolor': "rgba(248,249,250,0.5)"},
                'bar': {'color': "#ff1744"},
                'bgcolor': "rgba(0,0,0,0)",
                'bordercolor': "rgba(248,249,250,0.1)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(0,230,118,0.15)'},
                    {'range': [50, 80], 'color': 'rgba(255,234,0,0.15)'},
                    {'range': [80, 100], 'color': 'rgba(255,23,68,0.15)'}
                ],
            }
        ))
        fig.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(248,249,250,0.85)")
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col4:
        network_current = st.session_state.system_status["system_resources"]["network_load"]
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = network_current,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Network Load"},
            gauge = {
                'axis': {'range': [0, 100], 'tickcolor': "rgba(248,249,250,0.5)"},
                'bar': {'color': "#ffea00"},
                'bgcolor': "rgba(0,0,0,0)",
                'bordercolor': "rgba(248,249,250,0.1)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(0,230,118,0.15)'},
                    {'range': [50, 80], 'color': 'rgba(255,234,0,0.15)'},
                    {'range': [80, 100], 'color': 'rgba(255,23,68,0.15)'}
                ],
            }
        ))
        fig.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(248,249,250,0.85)")
        )
        st.plotly_chart(fig, use_container_width=True)

with performance_tabs[1]:
    # Response time and throughput charts
    response_df = pd.DataFrame({
        'Time': st.session_state.performance_metrics["timestamps"],
        'Response Time (ms)': st.session_state.performance_metrics["response_time"]
    })
    
    throughput_df = pd.DataFrame({
        'Time': st.session_state.performance_metrics["timestamps"],
        'Requests/min': st.session_state.performance_metrics["throughput"]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_resp = px.line(response_df, x='Time', y='Response Time (ms)', 
                           title='Average Response Time (Last 24 Hours)')
        fig_resp.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(248,249,250,0.85)'),
            margin=dict(l=10, r=10, t=40, b=10),
            height=300
        )
        fig_resp.update_traces(line=dict(color='#ff1744'))
        st.plotly_chart(fig_resp, use_container_width=True)
    
    with col2:
        fig_thru = px.line(throughput_df, x='Time', y='Requests/min', 
                         title='System Throughput (Last 24 Hours)')
        fig_thru.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(248,249,250,0.85)'),
            margin=dict(l=10, r=10, t=40, b=10),
            height=300
        )
        fig_thru.update_traces(line=dict(color='#00e676'))
        st.plotly_chart(fig_thru, use_container_width=True)
    
    # Current API metrics from real server
    st.markdown("### API Response Metrics")
    
    api_status = bridge.get_api_status()
    
    if api_status.get("success", False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                f"""
                <div class='tf-card'>
                    <h3>API Status Details</h3>
                    <table style="width: 100%;">
                        <tr>
                            <td style="padding: 0.5rem; color: var(--tf-text-secondary);">Service:</td>
                            <td style="padding: 0.5rem;">{api_status.get('data', {}).get('service', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 0.5rem; color: var(--tf-text-secondary);">Status:</td>
                            <td style="padding: 0.5rem;">
                                <span style="color: var(--tf-success);">●</span> {api_status.get('data', {}).get('status', 'N/A')}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 0.5rem; color: var(--tf-text-secondary);">Version:</td>
                            <td style="padding: 0.5rem;">{api_status.get('data', {}).get('version', 'N/A')}</td>
                        </tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            # API endpoint response time simulation
            endpoints = ["GET /api/status", "GET /api/v1/levy", "POST /api/v1/analyze"]
            resp_times = [42, 85, 130]
            
            endpoint_df = pd.DataFrame({
                'Endpoint': endpoints,
                'Response Time (ms)': resp_times
            })
            
            fig = px.bar(endpoint_df, x='Endpoint', y='Response Time (ms)', 
                        title='Endpoint Performance',
                        color='Response Time (ms)',
                        color_continuous_scale=['#00e676', '#ffea00', '#ff1744'])
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(248,249,250,0.85)'),
                margin=dict(l=10, r=10, t=40, b=10),
                height=250
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        render_alert(
            "API server is currently offline. Check server status or restart the server.",
            level="error"
        )

with performance_tabs[2]:
    # Service health status table
    st.markdown("### Microservice Health Status")
    
    # Create a styled services table
    services_data = st.session_state.system_status["services"]
    
    st.markdown(
        f"""
        <div class='tf-card'>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid var(--tf-border); text-align: left;">
                    <th style="padding: 0.75rem; color: var(--tf-text);">Service</th>
                    <th style="padding: 0.75rem; color: var(--tf-text);">Status</th>
                    <th style="padding: 0.75rem; color: var(--tf-text);">Response Time</th>
                    <th style="padding: 0.75rem; color: var(--tf-text);">Uptime</th>
                </tr>
        """,
        unsafe_allow_html=True
    )
    
    for service in services_data:
        # Set status color
        if service["status"] == "operational":
            status_color = "var(--tf-success)"
            status_text = "Operational"
        elif service["status"] == "degraded":
            status_color = "var(--tf-warning)"
            status_text = "Degraded"
        else:
            status_color = "var(--tf-error)"
            status_text = "Down"
        
        # Set response time color
        if service["response_time"] < 100:
            resp_color = "var(--tf-success)"
        elif service["response_time"] < 300:
            resp_color = "var(--tf-warning)"
        else:
            resp_color = "var(--tf-error)"
        
        st.markdown(
            f"""
            <tr style="border-bottom: 1px solid var(--tf-border-light);">
                <td style="padding: 0.75rem;">{service["name"]}</td>
                <td style="padding: 0.75rem;">
                    <span style="color: {status_color}; display: flex; align-items: center;">
                        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; 
                               background-color: {status_color}; margin-right: 0.5rem;"></span>
                        {status_text}
                    </span>
                </td>
                <td style="padding: 0.75rem; color: {resp_color};">{service["response_time"]} ms</td>
                <td style="padding: 0.75rem;">{service["uptime"]}%</td>
            </tr>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("</table></div>", unsafe_allow_html=True)
    
    # Service dependencies visualization
    st.markdown("### Service Dependency Map")
    
    # Create a network diagram of service dependencies
    service_nodes = ['API Gateway', 'Auth Service', 'Repository Service', 'Analysis Service', 'Protocol Server']
    service_edges = [
        ('API Gateway', 'Auth Service'), 
        ('API Gateway', 'Repository Service'),
        ('API Gateway', 'Analysis Service'),
        ('Repository Service', 'Protocol Server'),
        ('Analysis Service', 'Protocol Server'),
        ('Analysis Service', 'Repository Service')
    ]
    
    # Create networkx graph
    import networkx as nx
    G = nx.DiGraph()
    for node in service_nodes:
        G.add_node(node)
    for edge in service_edges:
        G.add_edge(edge[0], edge[1])
    
    # Calculate positions
    pos = nx.spring_layout(G, seed=42)
    
    # Create traces for edges
    edge_trace = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        # Find service status to color the edge
        source_service = next((s for s in services_data if s["name"] == edge[0]), None)
        if source_service:
            if source_service["status"] == "operational":
                edge_color = "rgba(0, 230, 118, 0.6)"
            elif source_service["status"] == "degraded":
                edge_color = "rgba(255, 234, 0, 0.6)"
            else:
                edge_color = "rgba(255, 23, 68, 0.6)"
        else:
            edge_color = "rgba(255, 255, 255, 0.3)"
        
        edge_trace.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=2, color=edge_color),
                hoverinfo='none',
                mode='lines'
            )
        )
    
    # Create trace for nodes
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        
        # Find service status to color the node
        service = next((s for s in services_data if s["name"] == node), None)
        if service:
            if service["status"] == "operational":
                node_color.append("#00e676")
            elif service["status"] == "degraded":
                node_color.append("#ffea00")
            else:
                node_color.append("#ff1744")
        else:
            node_color.append("#7c4dff")
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        marker=dict(
            size=15,
            color=node_color,
            line=dict(width=1, color='#121212')
        ),
        textfont=dict(
            family="Arial",
            size=10,
            color="rgba(248, 249, 250, 0.85)"
        )
    )
    
    # Create figure
    fig = go.Figure(data=edge_trace + [node_trace],
                  layout=go.Layout(
                      title="Service Dependencies",
                      titlefont=dict(size=16, color="#7c4dff"),
                      showlegend=False,
                      hovermode='closest',
                      margin=dict(b=20, l=5, r=5, t=40),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)',
                      annotations=[
                          dict(
                              text="Network graph showing service dependencies",
                              showarrow=False,
                              xref="paper", yref="paper",
                              x=0.01, y=0,
                              font=dict(size=10, color="rgba(248, 249, 250, 0.5)")
                          )
                      ]
                  ))
    st.plotly_chart(fig, use_container_width=True)

# Pipeline and workflow status
st.markdown('<div class="section-header">DevOps Pipeline Status</div>', unsafe_allow_html=True)

pipeline_data = st.session_state.system_status["pipeline_status"]

# Create a visual pipeline flow
st.markdown(
    """
    <div class='tf-card'>
        <h3>Current Pipeline Execution</h3>
        <div style="display: flex; justify-content: space-between; margin-top: 1.5rem;">
    """,
    unsafe_allow_html=True
)

for i, stage in enumerate(pipeline_data):
    # Determine stage status styling
    if stage["stage"] == "completed":
        stage_class = "completed"
        stage_bg = "rgba(0, 230, 118, 0.1)"
        stage_border = "1px solid var(--tf-success)"
        stage_icon = "✓"
        stage_icon_color = "var(--tf-success)"
        stage_progress = "100%"
    elif stage["stage"] == "in_progress":
        stage_class = "in-progress"
        stage_bg = "rgba(124, 77, 255, 0.1)"
        stage_border = "1px solid var(--tf-primary)"
        stage_icon = "●"
        stage_icon_color = "var(--tf-primary)"
        # Calculate random progress percentage for demo
        import random
        stage_progress = f"{random.randint(30, 80)}%"
    else:  # pending
        stage_class = "pending"
        stage_bg = "rgba(248, 249, 250, 0.05)"
        stage_border = "1px solid var(--tf-border)"
        stage_icon = "○"
        stage_icon_color = "var(--tf-text-tertiary)"
        stage_progress = "0%"
    
    # Add connector line if not the last item
    connector = "" if i == len(pipeline_data) - 1 else """
        <div style="height: 2px; flex-grow: 1; background: linear-gradient(to right, 
                 var(--tf-border), var(--tf-border-light)); 
                 margin: 0 -10px; align-self: center;"></div>
    """
    
    # Set duration text
    if stage["duration"]:
        duration_text = f"{stage['duration']}s"
    else:
        duration_text = "Pending"
    
    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; align-items: center; position: relative; flex: 1;">
            <div style="background: {stage_bg}; border: {stage_border}; border-radius: 0.5rem; 
                      padding: 1rem; width: 90%; position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="color: {stage_icon_color}; margin-right: 0.5rem; font-size: 1.2rem;">{stage_icon}</span>
                    <span style="font-weight: 600;">{stage["name"]}</span>
                </div>
                <div style="margin: 0.75rem 0; height: 6px; background-color: rgba(248, 249, 250, 0.1); 
                          border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; width: {stage_progress}; background-color: {stage_icon_color}; 
                              border-radius: 3px;"></div>
                </div>
                <div style="color: var(--tf-text-tertiary); font-size: 0.8rem;">
                    Duration: {duration_text}
                </div>
            </div>
            {connector}
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("</div></div>", unsafe_allow_html=True)

# Activity and logs section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Recent System Activity")
    
    activity_data = st.session_state.system_status["recent_activity"]
    
    for activity in activity_data:
        # Format timestamp
        timestamp = activity["timestamp"]
        if (datetime.now() - timestamp).total_seconds() < 60:
            time_str = "Just now"
        elif (datetime.now() - timestamp).total_seconds() < 3600:
            minutes = int((datetime.now() - timestamp).total_seconds() / 60)
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = int((datetime.now() - timestamp).total_seconds() / 3600)
            time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        # Set status styling
        if activity["status"] == "success":
            status_color = "var(--tf-success)"
            status_icon = "✓"
        elif activity["status"] == "warning":
            status_color = "var(--tf-warning)"
            status_icon = "⚠"
        else:
            status_color = "var(--tf-error)"
            status_icon = "✕"
        
        # Create activity card
        st.markdown(
            f"""
            <div style="background-color: var(--tf-card-bg); border: 1px solid var(--tf-border);
                      border-left: 3px solid {status_color}; border-radius: 0.375rem;
                      padding: 0.75rem; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <div style="font-weight: 600; color: var(--tf-text);">
                        <span style="color: {status_color}; margin-right: 0.5rem;">{status_icon}</span>
                        {activity["service"]}
                    </div>
                    <div style="color: var(--tf-text-tertiary); font-size: 0.8rem;">
                        {time_str}
                    </div>
                </div>
                <div style="color: var(--tf-text-secondary); margin: 0.5rem 0;">
                    {activity["action"]}
                </div>
                {f'<div style="font-size: 0.8rem; color: {status_color}; margin-top: 0.25rem;">{activity["message"]}</div>' if "message" in activity else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

with col2:
    st.markdown("### Quick Actions")
    
    # Create buttons for common DevOps actions
    st.markdown(
        """
        <div style="background-color: var(--tf-card-bg); border: 1px solid var(--tf-border);
                  border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1rem;">
            <h4 style="margin-bottom: 1rem; color: var(--tf-primary);">System Operations</h4>
        """,
        unsafe_allow_html=True
    )
    
    # Refresh dashboard button
    if st.button("🔄 Refresh Dashboard"):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    # View detailed metrics
    if st.button("📊 View Detailed Metrics"):
        st.switch_page("pages/1_Sync_Service_Dashboard.py")
    
    # Check API status
    if st.button("📡 Check System Connectivity"):
        st.switch_page("API_Status")
        
    # Quick Workflow Map
    if st.button("🔍 Open Workflow Visualization"):
        st.switch_page("pages/4_Workflow_Visualization.py")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # System health summary
    st.markdown("### System Health Score")
    
    # Calculate a health score based on various metrics
    health_metrics = {
        "API Status": 100 if api_status.get("success", False) else 0,
        "Service Health": sum([100 if s["status"] == "operational" else 50 if s["status"] == "degraded" else 0 
                            for s in st.session_state.system_status["services"]]) / len(st.session_state.system_status["services"]),
        "Resource Usage": 100 - (sum([st.session_state.system_status["system_resources"][m] for m in ["cpu_usage", "memory_usage", "disk_usage"]]) / 3),
        "Workflow Success": st.session_state.system_status["workflows"]["success_rate"] * 100
    }
    
    overall_health = sum(health_metrics.values()) / len(health_metrics)
    
    # Determine health status color and message
    if overall_health >= 90:
        health_color = "var(--tf-success)"
        health_message = "Healthy"
    elif overall_health >= 75:
        health_color = "var(--tf-accent)"
        health_message = "Good"
    elif overall_health >= 60:
        health_color = "var(--tf-warning)"
        health_message = "Warning"
    else:
        health_color = "var(--tf-error)"
        health_message = "Critical"
    
    # Create a health score gauge
    fig = go.Figure(go.Indicator(
        domain = {'x': [0, 1], 'y': [0, 1]},
        value = overall_health,
        mode = "gauge+number+delta",
        title = {'text': "System Health"},
        delta = {'reference': 90},
        gauge = {
            'axis': {'range': [0, 100], 'tickcolor': "rgba(248,249,250,0.5)"},
            'bar': {'color': health_color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "rgba(248,249,250,0.1)",
            'steps': [
                {'range': [0, 60], 'color': 'rgba(255,23,68,0.15)'},
                {'range': [60, 75], 'color': 'rgba(255,234,0,0.15)'},
                {'range': [75, 90], 'color': 'rgba(0,224,224,0.15)'},
                {'range': [90, 100], 'color': 'rgba(0,230,118,0.15)'}
            ],
            'threshold': {
                'line': {'color': "rgba(248,249,250,0.5)", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(248,249,250,0.85)")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Health score summary
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: -1rem; margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; font-weight: 600; color: {health_color};">
                {health_message}
            </div>
            <div style="font-size: 0.8rem; color: var(--tf-text-tertiary);">
                Last updated: {st.session_state.last_refresh.strftime("%H:%M:%S")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Help and documentation link
st.markdown(
    """
    <div style="background-color: var(--tf-card-bg); border: 1px solid var(--tf-border);
              border-radius: 0.75rem; padding: 1.25rem; margin-top: 2rem; text-align: center;">
        <div style="color: var(--tf-text-secondary); margin-bottom: 0.5rem;">
            Need help using the TerraFusion Platform?
        </div>
        <div>
            <a href="#" style="color: var(--tf-primary); text-decoration: none; font-weight: 600;">
                View Documentation →
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Footer with version information
st.markdown(
    """
    <div class="footer">
        <div>TerraFusion Platform v1.2.0</div>
        <div style="margin-top: 0.5rem; font-size: 0.7rem;">© 2025 TerraFusion, Inc. All rights reserved.</div>
    </div>
    """,
    unsafe_allow_html=True
)