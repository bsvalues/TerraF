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
    layout="wide",
    initial_sidebar_state="expanded"
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

with tab2:
    st.header("Repository Performance")
    
    # Get current repository metrics
    repo_metrics = metrics.get("repository", {}).get("metrics", {})
    source_metrics = repo_metrics.get("source", {})
    target_metrics = repo_metrics.get("target", {})
    
    # Create columns for source and target
    st.subheader("Repository Health Status")
    repo_col1, repo_col2 = st.columns(2)
    
    with repo_col1:
        st.markdown("#### Source Repository")
        source_cpu = source_metrics.get("cpu_utilization", 0)
        source_memory = source_metrics.get("memory_utilization", 0)
        source_health = metrics.get("interpretation", {}).get("source_repo_health", "healthy")
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.markdown(create_metric_card(
                "CPU Utilization", 
                f"{source_cpu:.1f}", 
                unit="%", 
                health_status=source_health
            ), unsafe_allow_html=True)
        with s_col2:
            st.markdown(create_metric_card(
                "Memory Utilization", 
                f"{source_memory:.1f}", 
                unit="%", 
                health_status=source_health
            ), unsafe_allow_html=True)
            
        # Additional metrics for advanced view
        if show_advanced:
            s_col3, s_col4 = st.columns(2)
            with s_col3:
                execution_time = source_metrics.get("avg_execution_time_ms", 0)
                st.markdown(create_metric_card(
                    "Average Execution Time", 
                    f"{execution_time:.2f}", 
                    unit="ms"
                ), unsafe_allow_html=True)
            with s_col4:
                active_connections = source_metrics.get("active_connections", 0)
                st.markdown(create_metric_card(
                    "Active Connections", 
                    f"{active_connections}"
                ), unsafe_allow_html=True)
    
    with repo_col2:
        st.markdown("#### Target Repository")
        target_cpu = target_metrics.get("cpu_utilization", 0)
        target_memory = target_metrics.get("memory_utilization", 0)
        target_health = metrics.get("interpretation", {}).get("target_repo_health", "healthy")
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.markdown(create_metric_card(
                "CPU Utilization", 
                f"{target_cpu:.1f}", 
                unit="%", 
                health_status=target_health
            ), unsafe_allow_html=True)
        with t_col2:
            st.markdown(create_metric_card(
                "Memory Utilization", 
                f"{target_memory:.1f}", 
                unit="%", 
                health_status=target_health
            ), unsafe_allow_html=True)
            
        # Additional metrics for advanced view
        if show_advanced:
            t_col3, t_col4 = st.columns(2)
            with t_col3:
                execution_time = target_metrics.get("avg_execution_time_ms", 0)
                st.markdown(create_metric_card(
                    "Average Execution Time", 
                    f"{execution_time:.2f}", 
                    unit="ms"
                ), unsafe_allow_html=True)
            with t_col4:
                active_connections = target_metrics.get("active_connections", 0)
                st.markdown(create_metric_card(
                    "Active Connections", 
                    f"{active_connections}"
                ), unsafe_allow_html=True)
    
    # Risk factors
    risk_factors = metrics.get("interpretation", {}).get("risk_factors", [])
    if risk_factors:
        st.subheader("Risk Factors")
        for risk in risk_factors:
            st.warning(risk)
            
    # Recommendations
    recommendations = metrics.get("repository", {}).get("recommendations", [])
    if recommendations:
        st.subheader("Performance Recommendations")
        for rec in recommendations:
            st.info(f"{rec.get('description')} (Priority: {rec.get('severity', 'low')})")

with tab3:
    st.header("Batch Processing Optimization")
    
    # Get batch configuration and metrics
    batch_metrics = metrics.get("batch_processing", {})
    optimal_batch_sizes = metrics.get("optimal_batch_sizes", {}).get("optimal_batch_sizes", {})
    
    # Display optimal batch sizes
    st.subheader("Optimal Batch Sizes by Operation Type")
    
    # Create a bar chart for optimal batch sizes
    if optimal_batch_sizes:
        operation_types = list(optimal_batch_sizes.keys())
        batch_sizes = list(optimal_batch_sizes.values())
        
        df = pd.DataFrame({
            "Operation Type": operation_types,
            "Optimal Batch Size": batch_sizes
        })
        
        fig = px.bar(df, x="Operation Type", y="Optimal Batch Size",
                    title="Optimal Batch Sizes by Operation Type",
                    color="Optimal Batch Size",
                    color_continuous_scale=px.colors.sequential.Viridis)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No batch size optimization data available yet. Run a sync operation to generate this data.")
    
    # Display batch adjustment explanations
    adjustment_explanations = metrics.get("optimal_batch_sizes", {}).get("adjustment_explanations", [])
    if adjustment_explanations:
        st.subheader("Batch Size Adjustment Logic")
        for explanation in adjustment_explanations:
            st.info(explanation)
    
    # Advanced batch metrics
    if show_advanced and batch_metrics:
        st.subheader("Batch Processing Performance")
        
        a_col1, a_col2, a_col3 = st.columns(3)
        
        with a_col1:
            processing_rate = batch_metrics.get("processing_rate", 0)
            st.markdown(create_metric_card(
                "Processing Rate", 
                f"{processing_rate:.2f}", 
                unit="records/sec"
            ), unsafe_allow_html=True)
            
        with a_col2:
            avg_batch_duration = batch_metrics.get("avg_batch_duration", 0)
            st.markdown(create_metric_card(
                "Average Batch Duration", 
                f"{avg_batch_duration:.2f}", 
                unit="seconds"
            ), unsafe_allow_html=True)
            
        with a_col3:
            avg_batch_size = batch_metrics.get("avg_batch_size", 0)
            st.markdown(create_metric_card(
                "Average Batch Size", 
                f"{avg_batch_size:.0f}", 
                unit="records"
            ), unsafe_allow_html=True)

# Sync History Section
st.header("Sync Operation History")

if st.session_state.sync_history:
    for i, history_item in enumerate(reversed(st.session_state.sync_history)):
        with st.expander(f"{history_item['type']} - {history_item['timestamp']}", expanded=(i==0)):
            h_col1, h_col2, h_col3 = st.columns(3)
            
            with h_col1:
                st.metric("Records Processed", history_item.get("records_processed", 0))
                
            with h_col2:
                status = "✅ Success" if history_item.get("success", False) else "❌ Failed"
                st.write("Status:", status)
                
            with h_col3:
                if "performance" in history_item and "batch_processing_rate" in history_item["performance"]:
                    st.metric("Processing Rate", f"{history_item['performance']['batch_processing_rate']:.2f} records/sec")
                    
            if "performance" in history_item and show_advanced:
                st.write("Optimal batch size for next sync:", history_item["performance"].get("optimal_batch_size", "N/A"))
else:
    st.info("No sync operations have been performed yet.")

# Refresh data
if st.button("Refresh Metrics"):
    st.session_state.performance_metrics.append(
        st.session_state.sync_service.get_performance_metrics()
    )
    st.rerun()