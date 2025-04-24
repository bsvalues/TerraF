"""
SyncService UI

This module provides a Streamlit UI for the SyncService component.
"""

import json
import time
import datetime
import requests
import pandas as pd
import streamlit as st
from typing import Dict, Any, List, Optional

# Define constants
API_BASE_URL = "http://localhost:5001"  # The FastAPI service URL


def init_session_state():
    """Initialize session state variables."""
    if "sync_history" not in st.session_state:
        st.session_state.sync_history = []
    if "last_sync_time" not in st.session_state:
        st.session_state.last_sync_time = None
    if "sync_in_progress" not in st.session_state:
        st.session_state.sync_in_progress = False
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


def fetch_sync_status():
    """Fetch sync status from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/sync/status", timeout=5)
        response.raise_for_status()
        status_data = response.json()
        
        st.session_state.last_sync_time = status_data.get("last_sync_time")
        st.session_state.sync_history = status_data.get("sync_history", [])
        
        return status_data
    except Exception as e:
        st.session_state.error_message = f"Failed to fetch sync status: {str(e)}"
        # For demo, use mock data when API is not available
        return {
            "last_sync_time": datetime.datetime.now().isoformat(),
            "sync_history": [
                {
                    "type": "incremental",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "success": True,
                    "records_processed": 5,
                    "records_succeeded": 5
                },
                {
                    "type": "full",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
                    "success": True,
                    "records_processed": 42,
                    "records_succeeded": 42
                }
            ],
            "active": True,
            "version": "1.0.0 (Demo)"
        }


def perform_sync(sync_type: str) -> Dict[str, Any]:
    """
    Perform a sync operation.
    
    Args:
        sync_type: Either "full" or "incremental"
        
    Returns:
        Dictionary with sync results
    """
    st.session_state.sync_in_progress = True
    st.session_state.error_message = None
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text(f"Starting {sync_type} sync...")
        progress_bar.progress(10)
        time.sleep(0.5)  # Simulate network delay
        
        # Make API request
        url = f"{API_BASE_URL}/sync/{sync_type}"
        response = requests.post(url, timeout=30)
        response.raise_for_status()
        
        # Parse results
        result = response.json()
        
        # Update progress
        progress_bar.progress(100)
        status_text.text(f"{sync_type.capitalize()} sync completed successfully!")
        
        # Update session state
        st.session_state.last_sync_time = result.get("end_time")
        
        # Get updated sync history
        fetch_sync_status()
        
        return result
    except Exception as e:
        st.session_state.error_message = f"Sync failed: {str(e)}"
        progress_bar.progress(100)
        status_text.text("Sync failed!")
        
        # For demo, return mock data when API is not available
        return {
            "success": False,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "error_details": [{"error": str(e), "type": "Exception"}],
            "warnings": [],
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": datetime.datetime.now().isoformat(),
            "duration_seconds": 0.1
        }
    finally:
        st.session_state.sync_in_progress = False


def display_sync_history(history: List[Dict[str, Any]]):
    """Display sync history as a table."""
    if not history:
        st.info("No sync history available.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(history)
    
    # Format timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Add success icons
    df['status'] = df['success'].apply(lambda x: "✅" if x else "❌")
    
    # Reorder and rename columns
    df = df[['timestamp', 'type', 'records_processed', 'records_succeeded', 'status']]
    df.columns = ['Timestamp', 'Type', 'Processed', 'Succeeded', 'Status']
    
    # Display the table
    st.dataframe(df, use_container_width=True)


def display_sync_details(result: Dict[str, Any]):
    """Display detailed sync results."""
    if not result:
        return
    
    with st.expander("Sync Details", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Records Processed",
                result.get("records_processed", 0)
            )
        with col2:
            st.metric(
                "Records Succeeded",
                result.get("records_succeeded", 0)
            )
        with col3:
            st.metric(
                "Duration (seconds)",
                f"{result.get('duration_seconds', 0):.2f}"
            )
        
        # Show warnings
        warnings = result.get("warnings", [])
        if warnings:
            st.subheader("Warnings")
            for warning in warnings:
                st.warning(warning)
        
        # Show errors
        errors = result.get("error_details", [])
        if errors:
            st.subheader("Errors")
            for error in errors:
                error_msg = error.get("error", "Unknown error")
                error_type = error.get("type", "Error")
                record_id = error.get("record_id", "N/A")
                
                st.error(f"**{error_type}** (Record ID: {record_id}): {error_msg}")


def display_api_health():
    """Display API health status."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        response.raise_for_status()
        
        health_data = response.json()
        status = health_data.get("status", "unknown")
        components = health_data.get("components", {})
        
        if status == "ok":
            st.success("SyncService API is healthy")
        else:
            st.warning(f"SyncService API status: {status}")
        
        for component, details in components.items():
            component_status = details.get("status", "unknown")
            if component_status == "ok":
                st.success(f"{component.upper()}: Healthy")
            else:
                st.warning(f"{component.upper()}: {component_status}")
    except Exception as e:
        st.error(f"SyncService API is unavailable: {str(e)}")
        st.info("Demo mode: showing mock data")


def render_sync_service_tab():
    """Render the SyncService UI tab."""
    st.header("SyncService: PACS to CAMA Synchronization")
    
    # Initialize session state
    init_session_state()
    
    # Display API health status
    with st.sidebar:
        st.subheader("API Status")
        display_api_health()
        
        st.markdown("---")
        
        sync_status = fetch_sync_status()
        st.subheader("Sync Status")
        if sync_status.get("active"):
            st.success("SyncService is active")
        else:
            st.warning("SyncService is inactive")
        
        last_sync = sync_status.get("last_sync_time")
        if last_sync:
            try:
                last_sync_dt = datetime.datetime.fromisoformat(last_sync)
                st.info(f"Last sync: {last_sync_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                st.info(f"Last sync: {last_sync}")
        else:
            st.info("No previous sync recorded")
        
        version = sync_status.get("version", "unknown")
        st.text(f"Version: {version}")
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        # Incremental sync button
        st.button(
            "Perform Incremental Sync",
            on_click=lambda: perform_sync("incremental"),
            disabled=st.session_state.sync_in_progress,
            use_container_width=True
        )
    
    with col2:
        # Full sync button
        st.button(
            "Perform Full Sync",
            on_click=lambda: perform_sync("full"),
            disabled=st.session_state.sync_in_progress,
            use_container_width=True,
            type="primary"
        )
    
    # Show error message if any
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
    
    # Sync history section
    st.subheader("Sync History")
    display_sync_history(st.session_state.sync_history)
    
    # System architecture diagram
    st.subheader("SyncService Architecture")
    with st.expander("Architecture Diagram", expanded=False):
        st.markdown("""
        ```
        +---------------------+      +------------------------+      +---------------------+
        |                     |      |                        |      |                     |
        |  Legacy PACS System |      |  TerraFusion Platform  |      |  Modern CAMA System |
        |                     |      |     (SyncService)      |      |                     |
        |  +---------------+  |      |   +-----------------+  |      |  +---------------+  |
        |  |               |  |      |   |                 |  |      |  |               |  |
        |  | Property Data |<---------->| Change Detector  |  |      |  | Property Data |  |
        |  |               |  |      |   |                 |  |      |  |               |  |
        |  +---------------+  |      |   +-----------------+  |      |  +---------------+  |
        |                     |      |           |            |      |                     |
        |  +---------------+  |      |   +-----------------+  |      |  +---------------+  |
        |  |               |  |      |   |                 |  |      |  |               |  |
        |  | Change Log    |<---------->| Data Transformer |<---------->| Property      |  |
        |  |               |  |      |   |                 |  |      |  | Valuations    |  |
        |  +---------------+  |      |   +-----------------+  |      |  |               |  |
        |                     |      |           |            |      |  +---------------+  |
        |  +---------------+  |      |   +-----------------+  |      |                     |
        |  |               |  |      |   |                 |  |      |  +---------------+  |
        |  | Valuations    |<---------->| Data Validator   |<---------->| Audit Trail   |  |
        |  |               |  |      |   |                 |  |      |  |               |  |
        |  +---------------+  |      |   +-----------------+  |      |  +---------------+  |
        |                     |      |           |            |      |                     |
        +---------------------+      |   +-----------------+  |      +---------------------+
                                     |   |                 |  |
                                     |   | Self-Healing    |  |
                                     |   | Orchestrator    |  |
                                     |   |                 |  |
                                     |   +-----------------+  |
                                     |                        |
                                     +------------------------+
        ```
        
        The SyncService consists of several key components:
        
        1. **Change Detector** - Monitors the PACS system for changes in property data
        2. **Data Transformer** - Converts PACS data format to CAMA format with enrichment
        3. **Data Validator** - Ensures data integrity and consistency
        4. **Self-Healing Orchestrator** - Manages the sync process and handles errors
        
        The service supports both **full** and **incremental** synchronization modes.
        """)
    
    # Component details
    with st.expander("Component Details", expanded=False):
        st.markdown("""
        ### Change Detector
        - Monitors changes in the source PACS system through CDC (Change Data Capture)
        - Identifies new, updated, and deleted records
        - Optimizes change detection with timestamp-based tracking
        
        ### Data Transformer
        - Maps fields between source and target schemas
        - Transforms data formats (e.g., date formats, number formats)
        - Enriches data with AI-driven valuation insights
        - Handles nested data structures
        
        ### Data Validator
        - Validates data against business rules
        - Ensures referential integrity
        - Performs range checks and format validation
        - Identifies potential data quality issues
        
        ### Self-Healing Orchestrator
        - Manages the overall sync process
        - Handles error recovery and retries
        - Maintains sync state and transaction consistency
        - Provides monitoring and alerting
        """)
    
    # API endpoints
    with st.expander("API Endpoints", expanded=False):
        st.markdown("""
        The SyncService exposes the following API endpoints:
        
        - `POST /sync/full` - Perform a full sync of all data
        - `POST /sync/incremental` - Perform an incremental sync of changes
        - `GET /sync/status` - Get current sync status and history
        - `GET /health` - Check API health
        
        See the API documentation for details on request/response formats.
        """)


def add_sync_service_tab():
    """
    Add the SyncService tab to the main application.
    """
    return render_sync_service_tab