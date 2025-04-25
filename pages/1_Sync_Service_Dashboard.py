import streamlit as st
import time
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from sync_service import SyncService

# Set page configuration
st.set_page_config(
    page_title="SyncService Performance Monitor",
    page_icon="🔄",
    layout="wide"
)

# Define custom CSS
st.markdown("""
<style>
    .metric-card {
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        background-color: #f8f9fa;
    }
    .metric-title {
        font-size: 14px;
        font-weight: bold;
        color: #555;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .metric-unit {
        font-size: 12px;
        color: #777;
    }
    .metric-trend {
        font-size: 12px;
        margin-left: 5px;
    }
    .health-critical {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
    }
    .health-warning {
        background-color: #fff8e1;
        border-left: 5px solid #ffc107;
    }
    .health-moderate {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
    }
    .health-healthy {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
    }
    .sidebar-header {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .sync-history-item {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        background-color: #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sync_service' not in st.session_state:
    st.session_state.sync_service = SyncService()
    
if 'sync_history' not in st.session_state:
    st.session_state.sync_history = []
    
if 'performance_metrics' not in st.session_state:
    st.session_state.performance_metrics = []
    
if 'show_advanced' not in st.session_state:
    st.session_state.show_advanced = False

# Helper functions
def format_size(size_bytes):
    """Format bytes to a readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_health_class(health_status):
    """Get the CSS class based on health status"""
    if health_status == "critical":
        return "health-critical"
    elif health_status == "warning":
        return "health-warning"
    elif health_status == "moderate" or health_status == "elevated":
        return "health-moderate"
    else:
        return "health-healthy"

def create_metric_card(title, value, unit="", trend=None, health_status="healthy"):
    """Create a styled metric card"""
    health_class = get_health_class(health_status)
    trend_html = ""
    if trend:
        trend_icon = "↑" if trend > 0 else "↓"
        trend_color = "red" if trend > 0 and "cpu" in title.lower() else "green"
        trend_html = f'<span class="metric-trend" style="color: {trend_color}">{trend_icon} {abs(trend):.1f}%</span>'
    
    html = f"""
    <div class="metric-card {health_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value} <span class="metric-unit">{unit}</span> {trend_html}</div>
    </div>
    """
    return html

# Sidebar
st.sidebar.markdown('<div class="sidebar-header">SyncService Control Panel</div>', unsafe_allow_html=True)

# Sync Operations
st.sidebar.markdown("### Sync Operations")

sync_type = st.sidebar.selectbox(
    "Select Sync Type",
    ["Full Sync", "Incremental Sync", "Selective Sync"]
)

# Initialize collections variable
collections = ["code_repositories"]  # Default to code repositories

if sync_type == "Selective Sync":
    collections = st.sidebar.multiselect(
        "Select Repositories",
        ["code_repositories", "workflow_patterns", "architecture_templates", "code_metrics", "performance_data"],
        ["code_repositories"]
    )

advanced_options = st.sidebar.expander("Advanced Options")
with advanced_options:
    batch_size = st.slider("Initial Batch Size", 10, 500, 100)
    dynamic_sizing = st.checkbox("Enable Dynamic Batch Sizing", value=True)
    resource_aware = st.checkbox("Enable Resource-Aware Sizing", value=True)
    adaptive_learning = st.checkbox("Enable Adaptive Learning", value=True)
    
# Resource simulation section
st.sidebar.markdown("### Resource Simulation")
simulate_load = st.sidebar.checkbox("Simulate System Load", value=False)
if simulate_load:
    simulated_cpu = st.sidebar.slider("Simulated CPU Load (%)", 10, 95, 40)
    simulated_memory = st.sidebar.slider("Simulated Memory Load (%)", 10, 95, 50)
    simulated_disk_io = st.sidebar.slider("Simulated Disk I/O (%)", 5, 90, 30)
    
    # Add description of simulation
    st.sidebar.markdown("""
    <div style="font-size: 0.8em; color: #888;">
    This simulation allows you to test how batch sizes are adjusted under different system loads.
    Higher values will result in smaller batch sizes to prevent system overload.
    </div>
    """, unsafe_allow_html=True)
    
# Run sync button
if st.sidebar.button("Run Sync Operation"):
    # Prepare configuration based on advanced options
    config = {
        "batch_size": batch_size,
        "dynamic_sizing": dynamic_sizing,
        "resource_aware_sizing": resource_aware,
        "adaptive_learning": adaptive_learning,
        "workload_specific_sizing": True
    }
    
    # Add simulated resources if enabled
    if simulate_load:
        config["simulated_resources"] = {
            "cpu_percent": simulated_cpu,
            "memory_percent": simulated_memory,
            "disk_io_percent": simulated_disk_io
        }
        st.sidebar.info(f"Using simulated load: CPU {simulated_cpu}%, Memory {simulated_memory}%, Disk I/O {simulated_disk_io}%")
    
    # Update the sync service with the new configuration
    st.session_state.sync_service = SyncService(config)
    
    # Run the selected sync operation
    with st.spinner(f"Running {sync_type}..."):
        if sync_type == "Full Sync":
            result = st.session_state.sync_service.full_sync()
        elif sync_type == "Incremental Sync":
            result = st.session_state.sync_service.incremental_sync()
        else:  # Selective Sync
            result = st.session_state.sync_service.selective_sync(collections)
        
        # Add to history
        st.session_state.sync_history.append({
            "type": sync_type,
            "timestamp": result.get("end_time", ""),
            "records_processed": result.get("records_processed", 0),
            "success": result.get("success", False),
            "performance": result.get("performance_metrics", {})
        })
        
        # Get latest performance metrics with simulation values if enabled
        metrics = st.session_state.sync_service.get_performance_metrics()
        
        # If simulation is enabled, override the system resource values
        if simulate_load and "system_resources" in metrics:
            metrics["system_resources"]["cpu_percent"] = simulated_cpu
            metrics["system_resources"]["memory_percent"] = simulated_memory
            metrics["system_resources"]["disk_io_percent"] = simulated_disk_io
            metrics["interpretation"]["system_health"] = st.session_state.sync_service._interpret_system_health(metrics["system_resources"])
            
            # Recalculate optimal batch sizes based on simulated resources
            metrics["optimal_batch_sizes"] = st.session_state.sync_service._calculate_optimal_batch_sizes(
                metrics["system_resources"], 
                metrics.get("repository", {})
            )
            
            # Add explanation about simulation
            if "adjustment_explanations" not in metrics["optimal_batch_sizes"]:
                metrics["optimal_batch_sizes"]["adjustment_explanations"] = []
            metrics["optimal_batch_sizes"]["adjustment_explanations"].insert(
                0, f"Batch sizes calculated based on simulated resources: CPU {simulated_cpu}%, Memory {simulated_memory}%, Disk I/O {simulated_disk_io}%"
            )
        
        st.session_state.performance_metrics.append(metrics)
        
        st.success(f"{sync_type} completed successfully!")

# Toggle advanced view
st.sidebar.markdown("### Display Options")
show_advanced = st.sidebar.checkbox("Show Advanced Metrics", value=st.session_state.show_advanced)
st.session_state.show_advanced = show_advanced

# Add navigation back to homepage
if st.sidebar.button("Back to Home"):
    st.switch_page("app.py")

# Main content
st.title("SyncService Performance Dashboard")

# Info box explaining the dashboard
with st.expander("About this Dashboard", expanded=False):
    st.markdown("""
    ### Resource-Aware SyncService Dashboard
    
    This dashboard demonstrates the SyncService's advanced resource monitoring and dynamic batch sizing capabilities. The system automatically adjusts batch sizes based on:
    
    * **System Resources**: CPU, memory, and disk I/O utilization
    * **Repository Performance**: Processing times, connection efficiency, and storage load
    * **Workload Type**: Different operation types receive specialized batch sizing
    * **Historical Performance**: Learning from past operations for continuous optimization
    
    Try running different sync operations with various configurations to see how the system adapts batch sizes to maintain optimal performance.
    """)

# Performance Metrics Tabs
tab1, tab2, tab3 = st.tabs(["System Resources", "Repository Performance", "Batch Processing"])

with tab1:
    st.header("System Resource Monitoring")
    
    # Get current metrics
    metrics = st.session_state.sync_service.get_performance_metrics()
    system_resources = metrics.get("system_resources", {})
    system_health = metrics.get("interpretation", {}).get("system_health", {})
    
    # Create metrics grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_percent = system_resources.get("cpu_percent", 0)
        cpu_status = system_health.get("components", {}).get("cpu", "healthy")
        st.markdown(create_metric_card(
            "CPU Usage", 
            f"{cpu_percent:.1f}", 
            unit="%", 
            health_status=cpu_status
        ), unsafe_allow_html=True)
        
    with col2:
        memory_percent = system_resources.get("memory_percent", 0)
        memory_status = system_health.get("components", {}).get("memory", "healthy")
        st.markdown(create_metric_card(
            "Memory Usage", 
            f"{memory_percent:.1f}", 
            unit="%", 
            health_status=memory_status
        ), unsafe_allow_html=True)
        
    with col3:
        memory_used = system_resources.get("memory_used_mb", 0)
        st.markdown(create_metric_card(
            "Memory Used", 
            f"{memory_used:.1f}", 
            unit="MB"
        ), unsafe_allow_html=True)
        
    with col4:
        disk_io = system_resources.get("disk_io_percent", 0)
        disk_status = system_health.get("components", {}).get("disk_io", "healthy")
        st.markdown(create_metric_card(
            "Disk I/O", 
            f"{disk_io:.1f}", 
            unit="%", 
            health_status=disk_status
        ), unsafe_allow_html=True)
    
    # Resource interpretations
    if system_health.get("resource_interpretations"):
        st.subheader("Resource Insights")
        for interpretation in system_health.get("resource_interpretations", []):
            st.info(interpretation)
    
    # Resource usage over time chart (simulated)
    if st.session_state.performance_metrics:
        st.subheader("Resource Usage Over Time")
        
        # Prepare data
        timestamps = [i for i in range(len(st.session_state.performance_metrics))]
        cpu_values = [m.get("system_resources", {}).get("cpu_percent", 0) for m in st.session_state.performance_metrics]
        memory_values = [m.get("system_resources", {}).get("memory_percent", 0) for m in st.session_state.performance_metrics]
        disk_values = [m.get("system_resources", {}).get("disk_io_percent", 0) for m in st.session_state.performance_metrics]
        
        # Create dataframe
        df = pd.DataFrame({
            "Time": timestamps,
            "CPU Usage (%)": cpu_values,
            "Memory Usage (%)": memory_values,
            "Disk I/O (%)": disk_values
        })
        
        # Create chart
        fig = px.line(df, x="Time", y=["CPU Usage (%)", "Memory Usage (%)", "Disk I/O (%)"],
                     title="Resource Usage Over Time")
        fig.update_layout(height=400, legend_title="Resource")
        st.plotly_chart(fig, use_container_width=True)